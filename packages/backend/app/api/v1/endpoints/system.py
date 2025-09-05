"""System administration endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

from app.database import get_db
from app.models.user import User
from app.core.dependencies import get_current_user
from app.core.user_roles import UserRole
from app.services.persistent_metrics import persistent_metrics_collector
from app.core.decorators import validate_input, sanitize_response
from app.core.response_formatter import format_response

router = APIRouter()


class SyncRequest(BaseModel):
    """Request model for sync operations"""
    type: Literal["client", "all", "quick"]
    client_id: Optional[str] = None
    options: Optional[Dict[str, Any]] = None


@router.post("/sync")
@validate_input(max_string_length=100)
@sanitize_response()
@format_response(message="Sync operation completed successfully")
async def sync_operations(
    sync_request: SyncRequest,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_user(required_roles=[UserRole.ADMIN]))
):
    """Consolidated sync operations - replaces multiple sync endpoints"""
    
    try:
        if sync_request.type == "client":
            # Sync specific client
            if not sync_request.client_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="client_id is required for client sync"
                )
            
            result = await persistent_metrics_collector.sync_client_data(
                db, sync_request.client_id
            )
            
            return {
                "message": f"Successfully synced client {sync_request.client_id}",
                "type": "client",
                "client_id": sync_request.client_id,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        elif sync_request.type == "all":
            # Sync all clients
            result = await persistent_metrics_collector.sync_all_clients(db)
            
            return {
                "message": "Successfully synced all clients",
                "type": "all",
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        elif sync_request.type == "quick":
            # Quick sync all clients with cache warming
            from app.services.cache.redis import redis_client
            from app.services.metrics_service import metrics_service
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
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid sync type: {sync_request.type}"
            )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )


@router.get("/cache/stats")
@format_response(message="Cache statistics retrieved successfully")
async def get_cache_stats(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_user(required_roles=[UserRole.ADMIN]))
):
    """Get cache statistics (admin only)"""
    
    try:
        from app.services.cache.redis import redis_client
        from sqlalchemy import select
        from app.models import Client
        
        # Get Redis info
        redis_info = await redis_client.get_info()
        
        # Get all clients
        stmt = select(Client)
        result = await db.execute(stmt)
        clients = result.scalars().all()
        
        # Check cache status for each client
        cache_status = []
        total_cached = 0
        
        for client in clients:
            cache_key = f"enhanced_client_metrics:{client.id}"
            has_cache = await redis_client.exists(cache_key)
            
            if has_cache:
                total_cached += 1
                # Get cache TTL if available
                ttl = await redis_client.get_ttl(cache_key)
                cache_status.append({
                    "client_id": client.id,
                    "client_name": client.name,
                    "cached": True,
                    "ttl_seconds": ttl if ttl > 0 else None
                })
            else:
                cache_status.append({
                    "client_id": client.id,
                    "client_name": client.name,
                    "cached": False,
                    "ttl_seconds": None
                })
        
        # Check admin cache
        admin_cache_exists = await redis_client.exists("admin_metrics:overview")
        
        return {
            "redis_info": {
                "connected": redis_info.get("connected", False),
                "used_memory": redis_info.get("used_memory_human", "Unknown"),
                "total_keys": redis_info.get("db0", {}).get("keys", 0) if redis_info.get("db0") else 0
            },
            "cache_summary": {
                "total_clients": len(clients),
                "cached_clients": total_cached,
                "cache_hit_rate": round((total_cached / len(clients)) * 100, 1) if clients else 0,
                "admin_cache_exists": admin_cache_exists
            },
            "client_cache_status": cache_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache stats: {str(e)}"
        )


@router.delete("/cache")
@format_response(message="Cache cleared successfully")
async def clear_cache(
    client_id: Optional[str] = Query(None, description="Specific client ID to clear"),
    pattern: Optional[str] = Query(None, description="Cache pattern to clear"),
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_user(required_roles=[UserRole.ADMIN]))
):
    """Clear cache with optional filtering (admin only)"""
    
    try:
        from app.services.cache.redis import redis_client
        
        cleared_keys = 0
        
        if client_id:
            # Clear specific client cache
            patterns = [
                f"enhanced_client_metrics:{client_id}",
                f"client_metrics:{client_id}"
            ]
            
            for pattern_key in patterns:
                if await redis_client.exists(pattern_key):
                    await redis_client.delete(pattern_key)
                    cleared_keys += 1
            
            return {
                "message": f"Cache cleared for client {client_id}",
                "client_id": client_id,
                "cleared_keys": cleared_keys,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        elif pattern:
            # Clear by pattern
            cleared_keys = await redis_client.clear_pattern(pattern)
            
            return {
                "message": f"Cache cleared for pattern: {pattern}",
                "pattern": pattern,
                "cleared_keys": cleared_keys,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        else:
            # Clear all cache
            patterns = [
                "enhanced_client_metrics:*",
                "client_metrics:*",
                "admin_metrics:*"
            ]
            
            for cache_pattern in patterns:
                cleared_keys += await redis_client.clear_pattern(cache_pattern)
            
            return {
                "message": "All cache cleared",
                "cleared_keys": cleared_keys,
                "timestamp": datetime.utcnow().isoformat()
            }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )


@router.get("/tasks/{task_id}")
@format_response(message="Task status retrieved successfully")
async def get_task_status(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user(required_roles=[UserRole.ADMIN, UserRole.CLIENT]))
):
    """Get task status - admin and client users can check task status"""
    
    try:
        from celery.result import AsyncResult
        from app.core.celery_app import celery_app
        
        # Get task result
        task_result = AsyncResult(task_id, app=celery_app)
        
        # Basic task info
        task_info = {
            "task_id": task_id,
            "status": task_result.status,
            "ready": task_result.ready(),
            "successful": task_result.successful() if task_result.ready() else None,
            "failed": task_result.failed() if task_result.ready() else None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add result or error info if available
        if task_result.ready():
            if task_result.successful():
                task_info["result"] = task_result.result
            elif task_result.failed():
                task_info["error"] = str(task_result.info)
        else:
            # Task is still running, check for progress info
            if hasattr(task_result, 'info') and task_result.info:
                task_info["progress"] = task_result.info
        
        return task_info
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}"
        )


@router.get("/worker-stats")
@format_response(message="Worker statistics retrieved successfully")
async def get_worker_stats(
    admin_user: User = Depends(get_current_user(required_roles=[UserRole.ADMIN]))
):
    """Get Celery worker statistics (admin only)"""
    
    try:
        from app.core.celery_app import celery_app
        
        # Get active workers
        inspect = celery_app.control.inspect()
        
        # Get worker stats
        stats = inspect.stats()
        active_tasks = inspect.active()
        scheduled_tasks = inspect.scheduled()
        reserved_tasks = inspect.reserved()
        
        # Format response
        worker_info = []
        total_active_tasks = 0
        total_scheduled_tasks = 0
        total_reserved_tasks = 0
        
        if stats:
            for worker_name, worker_stats in stats.items():
                active_count = len(active_tasks.get(worker_name, [])) if active_tasks else 0
                scheduled_count = len(scheduled_tasks.get(worker_name, [])) if scheduled_tasks else 0
                reserved_count = len(reserved_tasks.get(worker_name, [])) if reserved_tasks else 0
                
                total_active_tasks += active_count
                total_scheduled_tasks += scheduled_count
                total_reserved_tasks += reserved_count
                
                worker_info.append({
                    "worker_name": worker_name,
                    "status": "online",
                    "active_tasks": active_count,
                    "scheduled_tasks": scheduled_count,
                    "reserved_tasks": reserved_count,
                    "total_tasks": worker_stats.get("total", {}),
                    "pool_info": {
                        "max_concurrency": worker_stats.get("pool", {}).get("max-concurrency"),
                        "processes": worker_stats.get("pool", {}).get("processes")
                    }
                })
        
        return {
            "workers": worker_info,
            "summary": {
                "total_workers": len(worker_info),
                "online_workers": len(worker_info),  # All returned workers are online
                "total_active_tasks": total_active_tasks,
                "total_scheduled_tasks": total_scheduled_tasks,
                "total_reserved_tasks": total_reserved_tasks
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        # Return empty stats if Celery is not available
        return {
            "workers": [],
            "summary": {
                "total_workers": 0,
                "online_workers": 0,
                "total_active_tasks": 0,
                "total_scheduled_tasks": 0,
                "total_reserved_tasks": 0
            },
            "error": f"Failed to get worker stats: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }