"""API endpoints for Celery task management and monitoring with service layer protection"""

import asyncio
import logging
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.core.dependencies import get_current_user
from app.core.user_roles import UserRole, RolePermissions
from app.core.decorators import validate_input, sanitize_response
from app.core.response_formatter import format_response
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
@format_response(message="Task status retrieved successfully")
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user())
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
@format_response(message="Worker statistics retrieved successfully")
async def get_worker_stats(
    admin_user: User = Depends(get_current_user(required_roles=[UserRole.ADMIN]))
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


# Metrics Collection Tasks (duplicates removed)


@router.post("/aggregation/daily")
@sanitize_response()
@format_response(message="Daily aggregation triggered successfully")
async def trigger_daily_aggregation(
    admin_user: User = Depends(get_current_user(required_roles=[UserRole.ADMIN]))
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


@router.post("/aggregation/trigger")
@validate_input(max_string_length=50)
@sanitize_response()
@format_response(message="Aggregation triggered successfully")
async def trigger_custom_aggregation(
    target_date: Optional[str] = None,
    admin_user: User = Depends(get_current_user(required_roles=[UserRole.ADMIN]))
) -> Dict[str, Any]:
    """Trigger custom aggregation with optional target date (admin only)"""
    try:
        from app.tasks.aggregation_tasks import compute_daily_aggregations
        from datetime import date, timedelta
        
        # Default to yesterday if no date provided
        if target_date:
            computation_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        else:
            computation_date = date.today() - timedelta(days=1)
        
        # Trigger the aggregation task
        task = compute_daily_aggregations.delay(computation_date.isoformat())
        
        return {
            "message": f"Aggregation triggered for {computation_date.isoformat()}",
            "task_id": task.id,
            "target_date": computation_date.isoformat(),
            "status": "queued"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger aggregation: {str(e)}"
        )


# Sync Operations (moved from system.py and clients.py)
@router.post("/sync/client/{client_id}")
@validate_input(max_string_length=100)
@sanitize_response()
@format_response(message="Client sync triggered successfully")
async def trigger_client_sync_by_id(
    client_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user())
) -> Dict[str, Any]:
    """Trigger sync for a specific client - moved from clients.py"""
    # Rate limiting for sync operations
    if not await TaskServiceMixin._check_task_rate_limit(current_user.id, "sync_client", limit=5, window=300):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded for sync operations"
        )
    
    # Verify client access
    if not RolePermissions.is_admin(current_user.role) and current_user.client_id != client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to trigger sync for this client"
        )
    
    from app.services.client_service import ClientService
    client_service = ClientService()
    client = await client_service.get_client_by_id(db, client_id, use_cache=False)
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    if not client.n8n_api_url or not client.n8n_api_key_encrypted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client n8n configuration not found. Please configure n8n API first."
        )
    
    try:
        # Use the client service immediate sync method
        sync_result = await client_service._immediate_sync_n8n_data(db, client)
        await TaskServiceMixin._log_task_operation("sync_client", current_user.id, f"client_id: {client_id}")
        
        return {
            "message": f"Sync completed successfully for client {client_id}",
            "client_id": client_id,
            "sync_result": sync_result,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        await TaskServiceMixin._log_task_operation("sync_client", current_user.id, f"client_id: {client_id}, error: {str(e)}", success=False)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )


@router.post("/sync/all")
@sanitize_response()
@format_response(message="Sync for all clients triggered successfully")
async def trigger_all_sync(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_user(required_roles=[UserRole.ADMIN]))
) -> Dict[str, Any]:
    """Trigger sync for all clients (admin only) - moved from system.py"""
    try:
        from app.services.persistent_metrics import persistent_metrics_collector
        result = await persistent_metrics_collector.sync_all_clients(db)
        
        return {
            "message": "Successfully synced all clients",
            "type": "all",
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync all clients: {str(e)}"
        )


@router.post("/sync/quick")
@sanitize_response()
@format_response(message="Quick sync with cache warming completed successfully")
async def trigger_quick_sync(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_user(required_roles=[UserRole.ADMIN]))
) -> Dict[str, Any]:
    """Quick sync all clients with cache warming (admin only) - moved from system.py"""
    try:
        from app.services.cache.redis import redis_client
        from app.services.metrics_service import metrics_service
        from app.services.persistent_metrics import persistent_metrics_collector
        from sqlalchemy import select
        from app.models import Client
        
        # Clear all cache first
        await redis_client.clear_pattern("enhanced_client_metrics:*")
        await redis_client.clear_pattern("client_metrics:*")
        await redis_client.clear_pattern("admin_metrics:*")
        
        # Sync all clients immediately
        results = []
        
        # Get all clients with n8n configuration
        stmt = select(Client).where(
            Client.n8n_api_url.isnot(None)
        )
        result = await db.execute(stmt)
        clients = result.scalars().all()
        
        for client in clients:
            try:
                sync_result = await persistent_metrics_collector.sync_client_data(
                    db, client.id
                )
                results.append({
                    "client_id": client.id,
                    "client_name": client.name,
                    "status": "success",
                    "result": sync_result
                })
                
                # Warm cache for this client immediately after sync
                try:
                    await metrics_service.get_client_metrics(db, client.id, use_cache=False)
                except Exception as cache_error:
                    logger.warning(f"Failed to warm cache for client {client.id}: {cache_error}")
                    
            except Exception as e:
                results.append({
                    "client_id": client.id,
                    "client_name": client.name,
                    "status": "error",
                    "error": str(e)
                })
        
        # Commit all changes
        await db.commit()
        
        # Warm admin metrics cache
        try:
            await metrics_service.get_admin_metrics(db)
        except Exception as cache_error:
            logger.warning(f"Failed to warm admin metrics cache: {cache_error}")
        
        successful = [r for r in results if r["status"] == "success"]
        failed = [r for r in results if r["status"] == "error"]
        
        return {
            "message": f"Quick sync completed: {len(successful)} successful, {len(failed)} failed",
            "type": "quick",
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
            "timestamp": datetime.utcnow().isoformat(),
            "cache_warmed": True
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quick sync failed: {str(e)}"
        )


@router.get("/health-check")
@sanitize_response()
@format_response(message="Health check triggered successfully")
async def trigger_health_check(
    current_user: User = Depends(get_current_user())
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


@router.post("/health-check")
@sanitize_response()
@format_response(message="Health check triggered successfully")
async def trigger_health_check(
    current_user: User = Depends(get_current_user())
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
