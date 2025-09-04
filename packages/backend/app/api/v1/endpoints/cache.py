"""Cache management endpoints with service layer protection"""

import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.dependencies import get_current_user
from app.core.user_roles import UserRole
from app.models.user import User
from app.services.cache.redis import redis_client
from app.core.response_formatter import format_response
from app.schemas.cache import CacheClearResponse, CacheStatsResponse, ClientCacheClearResponse

router = APIRouter()
logger = logging.getLogger(__name__)


class CacheServiceMixin:
    """Service layer mixin for cache operations"""
    
    @staticmethod
    async def _check_cache_rate_limit(user_id: str, operation: str, limit: int = 20, window: int = 300) -> bool:
        """Check rate limit for cache operations"""
        try:
            current_time = int(datetime.utcnow().timestamp())
            window_start = current_time - window
            rate_limit_key = f"rate_limit:cache:{operation}:{user_id}"
            
            pipe = redis_client.pipeline()
            pipe.zremrangebyscore(rate_limit_key, 0, window_start)
            pipe.zcard(rate_limit_key)
            pipe.zadd(rate_limit_key, {str(current_time): current_time})
            pipe.expire(rate_limit_key, window)
            
            results = await pipe.execute()
            current_requests = results[1]
            
            return current_requests < limit
        except Exception as e:
            logger.warning(f"Cache rate limiter error: {e}")
            return True  # Fail open
    
    @staticmethod
    async def _log_cache_operation(operation: str, user_id: str, details: str = None, success: bool = True):
        """Log cache operations for monitoring"""
        try:
            if success:
                logger.info(f"Cache operation: {operation} by admin {user_id} - {details or 'success'}")
            else:
                logger.warning(f"Cache operation failed: {operation} by admin {user_id} - {details or 'failed'}")
        except Exception as e:
            logger.error(f"Failed to log cache operation: {e}")


@router.delete("/client/{client_id}")
@format_response(message="Client cache cleared successfully")
async def clear_client_cache(
    client_id: str,
    admin_user: User = Depends(get_current_user(required_roles=[UserRole.ADMIN]))
):
    """Clear cache for a specific client (admin only) with service layer protection"""
    # Rate limiting for cache operations
    if not await CacheServiceMixin._check_cache_rate_limit(admin_user.id, "clear_client"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded for cache operations"
        )
    
    try:
        patterns = [
            f"service_cache:clients:*:{client_id}*",
            f"metrics_cache:*{client_id}*",
            f"workflow_cache:*{client_id}*",
            f"chatbot_cache:*{client_id}*"
        ]
        
        total_cleared = 0
        for pattern in patterns:
            try:
                keys = await redis_client.keys(pattern)
                if keys:
                    await redis_client.delete(*keys)
                    total_cleared += len(keys)
            except Exception as e:
                logger.warning(f"Failed to clear pattern {pattern}: {e}")
        
        await CacheServiceMixin._log_cache_operation("clear_client", admin_user.id, f"client_id: {client_id}, keys_cleared: {total_cleared}")
        
        return ClientCacheClearResponse(
            message=f"Cleared cache for client {client_id}",
            client_id=client_id,
            keys_cleared=total_cleared
        )
    except Exception as e:
        await CacheServiceMixin._log_cache_operation("clear_client", admin_user.id, f"client_id: {client_id}, error: {str(e)}", success=False)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )


@router.delete("/all")
@format_response(message="All cache cleared successfully")
async def clear_all_cache(
    admin_user: User = Depends(get_current_user(required_roles=[UserRole.ADMIN]))
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
    
    return CacheClearResponse(
        message="Cleared all metrics cache",
        keys_cleared=total_cleared
    )


@router.get("/stats")
@format_response(message="Cache statistics retrieved successfully")
async def get_cache_stats(
    admin_user: User = Depends(get_current_user(required_roles=[UserRole.ADMIN]))
):
    """Get cache statistics (admin only)"""
    try:
        # Count cached items
        workflow_keys = await redis_client.client.keys("workflows:*")
        execution_keys = await redis_client.client.keys("executions:*")
        metrics_keys = await redis_client.client.keys("client_metrics:*")
        
        return CacheStatsResponse(
            cached_workflows=len(workflow_keys),
            cached_executions=len(execution_keys),
            cached_metrics=len(metrics_keys),
            total_cached_items=len(workflow_keys) + len(execution_keys) + len(metrics_keys)
        )
    except Exception as e:
        return CacheStatsResponse(
            cached_workflows=0,
            cached_executions=0,
            cached_metrics=0,
            total_cached_items=0,
            error=str(e)
        )