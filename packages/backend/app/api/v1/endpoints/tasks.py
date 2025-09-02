"""API endpoints for Celery task management and monitoring with service layer protection"""

import asyncio
import logging
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List

from app.models.user import User
from app.core.dependencies import get_current_admin_user, get_current_user
from app.core.decorators import validate_input, sanitize_response
from app.services.cache.redis import redis_client

router = APIRouter()
logger = logging.getLogger(__name__)


class TaskServiceMixin:
    """Service layer mixin for task operations"""
    
    @staticmethod
    async def _check_task_rate_limit(user_id: str, operation: str, limit: int = 10, window: int = 60) -> bool:
        """Check rate limit for task operations"""
        try:
            current_time = int(datetime.utcnow().timestamp())
            window_start = current_time - window
            rate_limit_key = f"rate_limit:tasks:{operation}:{user_id}"
            
            pipe = redis_client.pipeline()
            pipe.zremrangebyscore(rate_limit_key, 0, window_start)
            pipe.zcard(rate_limit_key)
            pipe.zadd(rate_limit_key, {str(current_time): current_time})
            pipe.expire(rate_limit_key, window)
            
            results = await pipe.execute()
            current_requests = results[1]
            
            return current_requests < limit
        except Exception as e:
            logger.warning(f"Task rate limiter error: {e}")
            return True  # Fail open
    
    @staticmethod
    async def _log_task_operation(operation: str, user_id: str, details: str = None, success: bool = True):
        """Log task operations for monitoring"""
        try:
            log_data = {
                "operation": operation,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "success": success,
                "details": details
            }
            
            # Store in Redis for monitoring (expire after 7 days)
            task_log_key = f"task_log:{datetime.utcnow().strftime('%Y-%m-%d')}:{operation}:{user_id}"
            await redis_client.setex(task_log_key, 7 * 24 * 60 * 60, str(log_data))
            
            if success:
                logger.info(f"Task operation: {operation} by user {user_id} - {details or 'success'}")
            else:
                logger.warning(f"Task operation failed: {operation} by user {user_id} - {details or 'failed'}")
                
        except Exception as e:
            logger.error(f"Failed to log task operation: {e}")


# Task Status Monitoring
@router.get("/status/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get status of a specific task"""
    try:
        from app.core.celery_app import celery_app
        result = celery_app.AsyncResult(task_id)
        
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result if result.ready() else None,
            "info": result.info
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}"
        )


@router.get("/worker-stats")
async def get_worker_stats(
    admin_user: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """Get Celery worker statistics (admin only)"""
    try:
        from app.core.celery_app import celery_app
        inspect = celery_app.control.inspect()
        
        stats = inspect.stats()
        active_tasks = inspect.active()
        
        return {
            "workers": stats or {},
            "active_tasks": active_tasks or {}
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get worker stats: {str(e)}"
        )


# Metrics Collection Tasks
@router.post("/sync-client/{client_id}")
@validate_input(max_string_length=100)
@sanitize_response()
async def trigger_client_sync(
    client_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Trigger metrics sync for a specific client with service layer protection"""
    # Rate limiting for sync operations
    if not await TaskServiceMixin._check_task_rate_limit(current_user.id, "sync_client", limit=5, window=300):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded for sync operations"
        )
    
    # Verify client access
    if current_user.role != "admin" and current_user.client_id != client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to trigger sync for this client"
        )
    
    # Check if sync is already in progress
    sync_key = f"sync_in_progress:{client_id}"
    if await redis_client.get(sync_key):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Sync already in progress for this client"
        )
    
    try:
        # Set sync in progress flag (expires in 10 minutes)
        await redis_client.setex(sync_key, 600, "true")
        
        from app.tasks.metrics_tasks import sync_client_metrics
        task = sync_client_metrics.apply_async(args=[client_id], queue='metrics')
        
        await TaskServiceMixin._log_task_operation("sync_client", current_user.id, f"client_id: {client_id}, task_id: {task.id}")
        
        return {
            "message": f"Metrics sync started for client {client_id}",
            "task_id": task.id,
            "status": "pending"
        }
    except Exception as e:
        # Clear sync flag on error
        await redis_client.delete(sync_key)
        await TaskServiceMixin._log_task_operation("sync_client", current_user.id, f"client_id: {client_id}, error: {str(e)}", success=False)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start sync: {str(e)}"
        )


@router.post("/sync-all")
@sanitize_response()
async def trigger_all_clients_sync(
    admin_user: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """Trigger metrics sync for all clients (admin only)"""
    try:
        from app.tasks.metrics_tasks import sync_all_clients_metrics
        task = sync_all_clients_metrics.apply_async(queue='metrics')
        
        return {
            "message": "Metrics sync started for all clients",
            "task_id": task.id,
            "status": "pending"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start sync: {str(e)}"
        )


@router.post("/aggregation/daily")
@sanitize_response()
async def trigger_daily_aggregation(
    admin_user: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """Trigger daily aggregation computation (admin only)"""
    try:
        from app.tasks.aggregation_tasks import compute_daily_aggregations
        task = compute_daily_aggregations.apply_async(queue='aggregation')
        
        return {
            "message": "Daily aggregation started",
            "task_id": task.id,
            "status": "pending"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start daily aggregation: {str(e)}"
        )


@router.post("/health-check")
@sanitize_response()
async def trigger_health_check(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Trigger health check task"""
    try:
        from app.tasks.metrics_tasks import health_check
        task = health_check.apply_async(queue='default')
        
        return {
            "message": "Health check started",
            "task_id": task.id,
            "status": "pending"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start health check: {str(e)}"
        )