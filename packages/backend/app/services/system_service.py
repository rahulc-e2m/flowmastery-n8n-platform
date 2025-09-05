"""System Service for sync operations and system management with service layer protection"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.client import Client
from app.core.service_layer import BaseService, OperationContext, OperationType, OperationResult

logger = logging.getLogger(__name__)


class SystemService(BaseService):
    """Service for system operations with service layer protection"""
    
    def __init__(self):
        super().__init__()
        self._service_name = "system_service"
    
    @property
    def service_name(self) -> str:
        return self._service_name
    
    async def get_clients_for_sync(
        self,
        db: AsyncSession,
        context: OperationContext,
        with_n8n_config_only: bool = False
    ) -> OperationResult[List[Client]]:
        """Get clients for sync operations with service layer protection"""
        context.operation_type = OperationType.READ
        
        async def _get_clients_operation():
            cache_key = f"sync_clients:{'with_n8n' if with_n8n_config_only else 'all'}"
            
            # Try cache first
            cached_result = await self._get_from_cache(cache_key)
            if cached_result is not None:
                # Convert cached data back to Client objects
                clients = []
                for client_data in cached_result:
                    client = Client(**client_data)
                    clients.append(client)
                return clients
            
            # Get from database
            async with self._get_db_session() as db_session:
                if with_n8n_config_only:
                    # Get only clients with n8n configuration
                    stmt = select(Client).where(Client.n8n_api_url.isnot(None))
                else:
                    # Get all clients
                    stmt = select(Client)
                
                result = await db_session.execute(stmt)
                clients = result.scalars().all()
                
                # Cache the result
                client_data = []
                for client in clients:
                    client_data.append({
                        'id': client.id,
                        'name': client.name,
                        'n8n_api_url': client.n8n_api_url,
                        'created_at': client.created_at.isoformat() if client.created_at else None,
                        'created_by_admin_id': client.created_by_admin_id,
                        'n8n_api_key_encrypted': client.n8n_api_key_encrypted
                    })
                
                await self._set_cache(cache_key, client_data, ttl=300)  # 5 minutes cache
                
                return list(clients)
        
        return await self.execute_operation(_get_clients_operation, context)
    
    async def sync_client_data(
        self,
        db: AsyncSession,
        client_id: str,
        context: OperationContext
    ) -> OperationResult[Dict[str, Any]]:
        """Sync data for a specific client with service layer protection"""
        context.operation_type = OperationType.UPDATE
        
        async def _sync_client_operation():
            from app.services.persistent_metrics import persistent_metrics_collector
            
            # Validate client exists first
            async with self._get_db_session() as db_session:
                stmt = select(Client).where(Client.id == client_id)
                result = await db_session.execute(stmt)
                client = result.scalar_one_or_none()
                
                if not client:
                    raise ValueError(f"Client {client_id} not found")
            
            # Perform the sync using the existing persistent metrics collector
            sync_result = await persistent_metrics_collector.sync_client_data(db, client_id)
            
            # Invalidate related caches
            await self._invalidate_cache("sync_clients:*")
            await self._invalidate_cache(f"enhanced_client_metrics:{client_id}")
            await self._invalidate_cache(f"client_metrics:{client_id}")
            
            return {
                "message": f"Successfully synced client {client_id}",
                "client_id": client_id,
                "sync_result": sync_result,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return await self.execute_operation(_sync_client_operation, context)
    
    async def sync_all_clients(
        self,
        db: AsyncSession,
        context: OperationContext
    ) -> OperationResult[Dict[str, Any]]:
        """Sync data for all clients with service layer protection"""
        context.operation_type = OperationType.BULK_UPDATE
        
        async def _sync_all_operation():
            from app.services.persistent_metrics import persistent_metrics_collector
            
            # Perform the sync using the existing persistent metrics collector
            sync_result = await persistent_metrics_collector.sync_all_clients(db)
            
            # Invalidate related caches
            await self._invalidate_cache("sync_clients:*")
            await self._invalidate_cache("enhanced_client_metrics:*")
            await self._invalidate_cache("client_metrics:*")
            await self._invalidate_cache("admin_metrics:*")
            
            return {
                "message": "Successfully synced all clients",
                "sync_result": sync_result,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return await self.execute_operation(_sync_all_operation, context)
    
    async def quick_sync_with_cache_warm(
        self,
        db: AsyncSession,
        context: OperationContext
    ) -> OperationResult[Dict[str, Any]]:
        """Quick sync all clients with cache warming with service layer protection"""
        context.operation_type = OperationType.BULK_UPDATE
        
        async def _quick_sync_operation():
            from app.services.persistent_metrics import persistent_metrics_collector
            from app.services.cache.redis import redis_client
            from app.services.metrics_service import metrics_service
            
            # Clear all cache first
            await redis_client.clear_pattern("enhanced_client_metrics:*")
            await redis_client.clear_pattern("client_metrics:*")
            await redis_client.clear_pattern("admin_metrics:*")
            
            # Get clients with n8n configuration using service layer
            clients_result = await self.get_clients_for_sync(db, context, with_n8n_config_only=True)
            
            if not clients_result.success:
                raise ValueError(f"Failed to get clients: {clients_result.error}")
            
            clients = clients_result.data
            results = []
            
            for client in clients:
                try:
                    sync_result = await persistent_metrics_collector.sync_client_data(db, client.id)
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
            
            # Invalidate sync client cache to force refresh
            await self._invalidate_cache("sync_clients:*")
            
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
        
        return await self.execute_operation(_quick_sync_operation, context)


# Create the service instance
system_service = SystemService()
