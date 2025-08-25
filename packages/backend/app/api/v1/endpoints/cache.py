"""Cache management endpoints"""

from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_admin_user
from app.models.user import User
from app.services.cache.redis import redis_client

router = APIRouter()


@router.delete("/client/{client_id}")
async def clear_client_cache(
    client_id: int,
    admin_user: User = Depends(get_current_admin_user)
):
    """Clear cache for a specific client (admin only)"""
    patterns = [
        f"client_metrics:{client_id}",
        f"workflows:*",  # Clear all workflow caches
        f"executions:*"  # Clear all execution caches
    ]
    
    total_cleared = 0
    for pattern in patterns:
        cleared = await redis_client.clear_pattern(pattern)
        total_cleared += cleared
    
    return {
        "message": f"Cleared cache for client {client_id}",
        "keys_cleared": total_cleared
    }


@router.delete("/all")
async def clear_all_cache(
    admin_user: User = Depends(get_current_admin_user)
):
    """Clear all metrics cache (admin only)"""
    patterns = [
        "client_metrics:*",
        "workflows:*",
        "executions:*"
    ]
    
    total_cleared = 0
    for pattern in patterns:
        cleared = await redis_client.clear_pattern(pattern)
        total_cleared += cleared
    
    return {
        "message": "Cleared all metrics cache",
        "keys_cleared": total_cleared
    }


@router.get("/stats")
async def get_cache_stats(
    admin_user: User = Depends(get_current_admin_user)
):
    """Get cache statistics (admin only)"""
    try:
        # Count cached items
        workflow_keys = await redis_client.client.keys("workflows:*")
        execution_keys = await redis_client.client.keys("executions:*")
        metrics_keys = await redis_client.client.keys("client_metrics:*")
        
        return {
            "cached_workflows": len(workflow_keys),
            "cached_executions": len(execution_keys),
            "cached_metrics": len(metrics_keys),
            "total_cached_items": len(workflow_keys) + len(execution_keys) + len(metrics_keys)
        }
    except Exception as e:
        return {
            "error": str(e),
            "cached_workflows": 0,
            "cached_executions": 0,
            "cached_metrics": 0,
            "total_cached_items": 0
        }