"""API endpoints for Celery task management and monitoring"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
from datetime import date

from app.models.user import User
from app.core.dependencies import get_current_admin_user, get_current_user
from app.core.decorators import validate_input, sanitize_response

router = APIRouter()


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
    """Trigger metrics sync for a specific client"""
    # Verify client access
    if current_user.role != "admin" and current_user.client_id != client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to trigger sync for this client"
        )
    
    try:
        from app.tasks.metrics_tasks import sync_client_metrics
        task = sync_client_metrics.apply_async(args=[client_id], queue='metrics')
        
        return {
            "message": f"Metrics sync started for client {client_id}",
            "task_id": task.id,
            "status": "pending"
        }
    except Exception as e:
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