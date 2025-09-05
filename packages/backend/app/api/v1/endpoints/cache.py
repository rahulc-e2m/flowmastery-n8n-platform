"""Consolidated cache management endpoints with service layer protection"""

import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.dependencies import get_current_user
from app.core.user_roles import UserRole
from app.models.user import User
from app.services.cache.redis import redis_client
from app.core.response_formatter import format_response
from app.core.decorators import validate_input, sanitize_response

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


@router.get("/stats")
@format_response(message="Cache statistics retrieved successfully")
async def get_cache_stats(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_user(required_roles=[UserRole.ADMIN]))
):
    """Get comprehensive cache statistics (admin only) - consolidated from system.py"""
    
    # Rate limiting for cache operations
    if not await CacheServiceMixin._check_cache_rate_limit(admin_user.id, "stats"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded for cache operations"
        )
    
    try:
        from app.services.cache_service import cache_service
        from app.core.service_layer import OperationContext, OperationType
        
        # Create operation context
        context = OperationContext(
            operation_type=OperationType.READ,
            user_id=admin_user.id
        )
        
        # Use CacheService to get statistics
        result = await cache_service.get_cache_statistics(db, context)
        
        if not result.success:
            await CacheServiceMixin._log_cache_operation("stats", admin_user.id, f"error: {result.error}", success=False)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.error or "Failed to get cache stats"
            )
        
        await CacheServiceMixin._log_cache_operation("stats", admin_user.id, "Retrieved cache statistics successfully")
        return result.data
        
    except HTTPException:
        raise
    except Exception as e:
        await CacheServiceMixin._log_cache_operation("stats", admin_user.id, f"error: {str(e)}", success=False)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache stats: {str(e)}"
        )


@router.delete("/clear")
@format_response(message="Cache cleared successfully")
async def clear_cache(
    client_id: Optional[str] = Query(None, description="Specific client ID to clear"),
    pattern: Optional[str] = Query(None, description="Cache pattern to clear"),
    admin_user: User = Depends(get_current_user(required_roles=[UserRole.ADMIN]))
):
    """Clear cache with optional filtering (admin only) - consolidated from system.py"""
    
    # Rate limiting for cache operations
    if not await CacheServiceMixin._check_cache_rate_limit(admin_user.id, "clear"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded for cache operations"
        )
    
    try:
        cleared_keys = 0
        
        if client_id:
            # Clear specific client cache
            patterns = [
                f"enhanced_client_metrics:{client_id}",
                f"client_metrics:{client_id}",
                f"service_cache:clients:*:{client_id}*",
                f"metrics_cache:*{client_id}*",
                f"workflow_cache:*{client_id}*",
                f"chatbot_cache:*{client_id}*"
            ]
            
            for pattern_key in patterns:
                try:
                    if "*" in pattern_key:
                        # Pattern-based deletion
                        keys = await redis_client.keys(pattern_key)
                        if keys:
                            await redis_client.delete(*keys)
                            cleared_keys += len(keys)
                    else:
                        # Direct key deletion
                        if await redis_client.exists(pattern_key):
                            await redis_client.delete(pattern_key)
                            cleared_keys += 1
                except Exception as e:
                    logger.warning(f"Failed to clear pattern {pattern_key}: {e}")
            
            await CacheServiceMixin._log_cache_operation("clear_client", admin_user.id, f"client_id: {client_id}, keys_cleared: {cleared_keys}")
            
            return {
                "message": f"Cache cleared for client {client_id}",
                "client_id": client_id,
                "cleared_keys": cleared_keys,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        elif pattern:
            # Clear by pattern
            cleared_keys = await redis_client.clear_pattern(pattern)
            
            await CacheServiceMixin._log_cache_operation("clear_pattern", admin_user.id, f"pattern: {pattern}, keys_cleared: {cleared_keys}")
            
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
                "admin_metrics:*",
                "workflows:*",
                "executions:*",
                "service_cache:*",
                "metrics_cache:*",
                "workflow_cache:*",
                "chatbot_cache:*"
            ]
            
            for cache_pattern in patterns:
                try:
                    cleared = await redis_client.clear_pattern(cache_pattern)
                    cleared_keys += cleared
                except Exception as e:
                    logger.warning(f"Failed to clear pattern {cache_pattern}: {e}")
            
            await CacheServiceMixin._log_cache_operation("clear_all", admin_user.id, f"keys_cleared: {cleared_keys}")
            
            return {
                "message": "All cache cleared",
                "cleared_keys": cleared_keys,
                "timestamp": datetime.utcnow().isoformat()
            }
        
    except Exception as e:
        await CacheServiceMixin._log_cache_operation("clear", admin_user.id, f"error: {str(e)}", success=False)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )


@router.delete("/client/{client_id}")
@format_response(message="Client cache cleared successfully")
async def clear_client_cache(
    client_id: str,
    admin_user: User = Depends(get_current_user(required_roles=[UserRole.ADMIN]))
):
    """Clear cache for a specific client (admin only) - enhanced version"""
    # Rate limiting for cache operations
    if not await CacheServiceMixin._check_cache_rate_limit(admin_user.id, "clear_client"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded for cache operations"
        )
    
    try:
        # Comprehensive client cache patterns
        patterns = [
            f"enhanced_client_metrics:{client_id}",
            f"client_metrics:{client_id}",
            f"service_cache:clients:*:{client_id}*",
            f"metrics_cache:*{client_id}*",
            f"workflow_cache:*{client_id}*",
            f"chatbot_cache:*{client_id}*"
        ]
        
        total_cleared = 0
        for pattern in patterns:
            try:
                if "*" in pattern:
                    # Pattern-based deletion
                    keys = await redis_client.keys(pattern)
                    if keys:
                        await redis_client.delete(*keys)
                        total_cleared += len(keys)
                else:
                    # Direct key deletion
                    if await redis_client.exists(pattern):
                        await redis_client.delete(pattern)
                        total_cleared += 1
            except Exception as e:
                logger.warning(f"Failed to clear pattern {pattern}: {e}")
        
        await CacheServiceMixin._log_cache_operation("clear_client", admin_user.id, f"client_id: {client_id}, keys_cleared: {total_cleared}")
        
        return {
            "message": f"Cleared cache for client {client_id}",
            "client_id": client_id,
            "keys_cleared": total_cleared,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        await CacheServiceMixin._log_cache_operation("clear_client", admin_user.id, f"client_id: {client_id}, error: {str(e)}", success=False)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )


@router.post("/warm")
@sanitize_response()
@format_response(message="Cache warming completed successfully")
async def warm_cache(
    client_id: Optional[str] = Query(None, description="Specific client ID to warm"),
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_user(required_roles=[UserRole.ADMIN]))
):
    """Warm cache for clients (admin only)"""
    
    # Rate limiting for cache operations
    if not await CacheServiceMixin._check_cache_rate_limit(admin_user.id, "warm"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded for cache operations"
        )
    
    try:
        from app.services.cache_service import cache_service
        from app.core.service_layer import OperationContext, OperationType
        
        # Create operation context
        context = OperationContext(
            operation_type=OperationType.CREATE,
            user_id=admin_user.id
        )
        
        # Use CacheService to warm cache
        result = await cache_service.warm_cache(db, client_id, context)
        
        if not result.success:
            await CacheServiceMixin._log_cache_operation("warm", admin_user.id, f"error: {result.error}", success=False)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.error or "Cache warming failed"
            )
        
        operation_type = "warm_client" if client_id else "warm_all"
        details = f"client_id: {client_id}" if client_id else f"warmed: {result.data.get('warmed_clients', 0)}/{result.data.get('total_clients', 0)} clients"
        await CacheServiceMixin._log_cache_operation(operation_type, admin_user.id, details)
        
        return result.data
        
    except HTTPException:
        raise
    except Exception as e:
        await CacheServiceMixin._log_cache_operation("warm", admin_user.id, f"error: {str(e)}", success=False)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cache warming failed: {str(e)}"
        )
