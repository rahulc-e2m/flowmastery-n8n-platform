"""Cache Service for operational cache management with service layer protection"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.client import Client
from app.services.cache.redis import redis_client
from app.core.service_layer import BaseService, OperationContext, OperationType, OperationResult

logger = logging.getLogger(__name__)


class CacheService(BaseService):
    """Service for cache management operations with service layer protection"""
    
    def __init__(self):
        super().__init__()
        self._service_name = "cache_service"
    
    @property
    def service_name(self) -> str:
        return self._service_name
    
    async def get_cache_statistics(
        self,
        db: AsyncSession,
        context: OperationContext
    ) -> OperationResult[Dict[str, Any]]:
        """Get comprehensive cache statistics with service layer protection"""
        context.operation_type = OperationType.READ
        
        async def _get_stats_operation():
            # Try cache first for redis info
            cache_key = "cache_stats:redis_info"
            cached_redis_info = await self._get_from_cache(cache_key)
            
            if not cached_redis_info:
                # Get Redis info
                redis_info = await redis_client.get_info()
                await self._set_cache(cache_key, redis_info, ttl=30)  # Cache for 30 seconds
            else:
                redis_info = cached_redis_info
            
            # Get all clients with service layer protection
            async with self._get_db_session() as db_session:
                stmt = select(Client)
                result = await db_session.execute(stmt)
                clients = result.scalars().all()
            
            # Check cache status for each client
            cache_status = []
            total_cached = 0
            
            for client in clients:
                cache_key_client = f"enhanced_client_metrics:{client.id}"
                has_cache = await redis_client.exists(cache_key_client)
                
                if has_cache:
                    total_cached += 1
                    # Get cache TTL if available
                    ttl = await redis_client.get_ttl(cache_key_client)
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
        
        return await self.execute_operation(_get_stats_operation, context)
    
    async def clear_cache_pattern(
        self,
        pattern: str,
        context: OperationContext
    ) -> OperationResult[Dict[str, Any]]:
        """Clear cache by pattern with service layer protection"""
        context.operation_type = OperationType.DELETE
        
        async def _clear_operation():
            if pattern == "all":
                # Clear all cache patterns
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
                
                total_cleared = 0
                for cache_pattern in patterns:
                    try:
                        cleared = await redis_client.clear_pattern(cache_pattern)
                        total_cleared += cleared
                    except Exception as e:
                        logger.warning(f"Failed to clear pattern {cache_pattern}: {e}")
                
                return {
                    "message": "All cache cleared",
                    "cleared_keys": total_cleared,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                # Clear specific pattern
                cleared_keys = await redis_client.clear_pattern(pattern)
                
                return {
                    "message": f"Cache cleared for pattern: {pattern}",
                    "pattern": pattern,
                    "cleared_keys": cleared_keys,
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        return await self.execute_operation(_clear_operation, context)
    
    async def clear_client_cache(
        self,
        client_id: str,
        context: OperationContext
    ) -> OperationResult[Dict[str, Any]]:
        """Clear cache for a specific client with service layer protection"""
        context.operation_type = OperationType.DELETE
        
        async def _clear_client_operation():
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
            
            return {
                "message": f"Cleared cache for client {client_id}",
                "client_id": client_id,
                "keys_cleared": total_cleared,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return await self.execute_operation(_clear_client_operation, context)
    
    async def warm_cache(
        self,
        db: AsyncSession,
        client_id: Optional[str],
        context: OperationContext
    ) -> OperationResult[Dict[str, Any]]:
        """Warm cache for clients with service layer protection"""
        context.operation_type = OperationType.CREATE
        
        async def _warm_operation():
            from app.services.metrics_service import metrics_service
            
            if client_id:
                # Warm cache for specific client
                await metrics_service.get_client_metrics(db, client_id, use_cache=False)
                
                return {
                    "message": f"Cache warmed for client {client_id}",
                    "client_id": client_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                # Warm cache for all clients
                async with self._get_db_session() as db_session:
                    stmt = select(Client)
                    result = await db_session.execute(stmt)
                    clients = result.scalars().all()
                
                warmed_clients = []
                for client in clients:
                    try:
                        await metrics_service.get_client_metrics(db, client.id, use_cache=False)
                        warmed_clients.append(client.id)
                    except Exception as e:
                        logger.warning(f"Failed to warm cache for client {client.id}: {e}")
                
                # Warm admin metrics cache
                try:
                    await metrics_service.get_admin_metrics(db)
                except Exception as e:
                    logger.warning(f"Failed to warm admin metrics cache: {e}")
                
                return {
                    "message": "Cache warmed for all clients",
                    "warmed_clients": len(warmed_clients),
                    "total_clients": len(clients),
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        return await self.execute_operation(_warm_operation, context)


# Create the service instance
cache_service = CacheService()
