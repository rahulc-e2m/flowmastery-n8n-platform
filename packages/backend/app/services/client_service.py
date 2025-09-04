"""Enhanced Client service with service layer architecture"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.client import Client
from app.models.user import User
from app.core.security import encryption_manager
from app.schemas.client import ClientCreate, ClientUpdate, ClientN8nConfig
from app.services.n8n.client import N8nClient
from app.services.cache.redis import redis_client

logger = logging.getLogger(__name__)


class ServiceLayerMixin:
    """Mixin to add service layer capabilities to existing services"""
    
    def __init__(self):
        self._semaphore = asyncio.Semaphore(10)  # Max 10 concurrent operations
        self._rate_limits = {}
        self._circuit_breaker_failures = {}
        
    async def _check_rate_limit(self, key: str, limit: int = 100, window: int = 60) -> bool:
        """Check rate limit using Redis sliding window"""
        try:
            current_time = int(datetime.now(timezone.utc).timestamp())
            window_start = current_time - window
            
            # Use individual Redis operations instead of pipeline for now
            await redis_client.zremrangebyscore(key, 0, window_start)
            current_requests = await redis_client.zcard(key)
            await redis_client.zadd(key, {str(current_time): current_time})
            await redis_client.expire(key, window)
            
            return current_requests < limit
        except Exception as e:
            logger.warning(f"Rate limiter error: {e}")
            return True  # Fail open
    
    async def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get data from Redis cache"""
        try:
            value = await redis_client.get(f"service_cache:{key}")
            if value:
                import json
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None
    
    async def _set_cache(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set data in Redis cache"""
        try:
            import json
            serialized_value = json.dumps(value, default=str)
            await redis_client.setex(f"service_cache:{key}", ttl, serialized_value)
            return True
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            return False
    
    async def _invalidate_cache_pattern(self, pattern: str) -> bool:
        """Invalidate cache keys matching pattern"""
        try:
            keys = await redis_client.keys(f"service_cache:{pattern}")
            if keys:
                for key in keys:
                    await redis_client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")
            return False
    
    async def _check_circuit_breaker(self, service_name: str, threshold: int = 5, timeout: int = 60) -> bool:
        """Check if circuit breaker allows operation"""
        try:
            key = f"circuit_breaker:{service_name}"
            failure_count = await redis_client.get(f"{key}:failures")
            last_failure = await redis_client.get(f"{key}:last_failure")
            
            if not failure_count:
                return True
            
            failure_count = int(failure_count)
            if failure_count < threshold:
                return True
            
            if last_failure:
                last_failure_time = datetime.fromisoformat(last_failure)
                if datetime.now(timezone.utc) - last_failure_time > timedelta(seconds=timeout):
                    # Reset circuit breaker
                    await redis_client.delete(f"{key}:failures")
                    await redis_client.delete(f"{key}:last_failure")
                    return True
            
            return False
        except Exception as e:
            logger.warning(f"Circuit breaker error: {e}")
            return True  # Fail open
    
    async def _record_success(self, service_name: str):
        """Record successful operation"""
        try:
            key = f"circuit_breaker:{service_name}"
            await redis_client.delete(f"{key}:failures")
            await redis_client.delete(f"{key}:last_failure")
        except Exception as e:
            logger.warning(f"Success recording error: {e}")
    
    async def _record_failure(self, service_name: str):
        """Record failed operation"""
        try:
            key = f"circuit_breaker:{service_name}"
            await redis_client.increment(f"{key}:failures")
            await redis_client.set(f"{key}:last_failure", datetime.now(timezone.utc).isoformat(), expire=300)
            await redis_client.expire(f"{key}:failures", 300)  # 5 minutes
        except Exception as e:
            logger.warning(f"Failure recording error: {e}")
    
    @asynccontextmanager
    async def _protected_operation(self, operation_name: str, user_id: str = None):
        """Context manager for protected database operations"""
        # Rate limiting
        rate_limit_key = f"rate_limit:client_service:{user_id or 'system'}"
        if not await self._check_rate_limit(rate_limit_key):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        # Circuit breaker
        if not await self._check_circuit_breaker("client_service"):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service temporarily unavailable"
            )
        
        # Concurrency control
        async with self._semaphore:
            start_time = datetime.now(timezone.utc)
            try:
                yield
                await self._record_success("client_service")
                
                # Log slow operations
                execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
                if execution_time > 1.0:  # Log operations taking more than 1 second
                    logger.warning(f"Slow operation {operation_name}: {execution_time:.2f}s")
                    
            except Exception as e:
                await self._record_failure("client_service")
                logger.error(f"Operation {operation_name} failed: {e}")
                raise


class ClientService(ServiceLayerMixin):
    """Enhanced service for client operations with service layer protection"""
    
    def __init__(self):
        super().__init__()
    
    async def create_client(
        self,
        db: AsyncSession,
        client_data: ClientCreate,
        admin_user: User
    ) -> Client:
        """Create a new client with service layer protection"""
        async with self._protected_operation("create_client", admin_user.id):
            # Validate input
            if not client_data.name or len(client_data.name.strip()) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Client name cannot be empty"
                )
            
            # Check for duplicate names
            existing = await db.execute(
                select(Client).where(Client.name == client_data.name.strip())
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Client with this name already exists"
                )
            
            client = Client(
                name=client_data.name.strip(),
                created_by_admin_id=admin_user.id
            )
            
            db.add(client)
            await db.commit()
            await db.refresh(client)
            
            # Invalidate relevant caches
            await self._invalidate_cache_pattern("clients:*")
            
            logger.info(f"Created client {client.id} by admin {admin_user.id}")
            return client
    
    async def get_client_by_id(self, db: AsyncSession, client_id: str, use_cache: bool = True) -> Optional[Client]:
        """Get client by ID with caching"""
        cache_key = f"clients:get:{client_id}"
        
        # Try cache first
        if use_cache:
            cached_client = await self._get_from_cache(cache_key)
            if cached_client:
                logger.debug(f"Cache hit for client {client_id}")
                return Client(**cached_client) if isinstance(cached_client, dict) else cached_client
        
        async with self._protected_operation("get_client_by_id"):
            result = await db.execute(select(Client).where(Client.id == client_id))
            client = result.scalar_one_or_none()
            
            # Cache the result
            if use_cache and client:
                client_dict = {
                    "id": client.id,
                    "name": client.name,
                    "n8n_api_url": client.n8n_api_url,
                    "n8n_api_key_encrypted": client.n8n_api_key_encrypted,
                    "created_by_admin_id": client.created_by_admin_id,
                    "created_at": client.created_at.isoformat() if client.created_at else None,
                    "updated_at": client.updated_at.isoformat() if client.updated_at else None
                }
                await self._set_cache(cache_key, client_dict, ttl=300)  # 5 minutes
            
            return client
    
    async def get_all_clients(self, db: AsyncSession, use_cache: bool = True) -> List[Client]:
        """Get all clients with caching"""
        cache_key = "clients:list:all"
        
        # Try cache first
        if use_cache:
            cached_clients = await self._get_from_cache(cache_key)
            if cached_clients:
                logger.debug("Cache hit for all clients")
                return [Client(**client_data) for client_data in cached_clients]
        
        async with self._protected_operation("get_all_clients"):
            result = await db.execute(select(Client).order_by(Client.created_at.desc()))
            clients = list(result.scalars().all())
            
            # Cache the result
            if use_cache and clients:
                clients_data = []
                for client in clients:
                    client_dict = {
                        "id": client.id,
                        "name": client.name,
                        "n8n_api_url": client.n8n_api_url,
                        "n8n_api_key_encrypted": client.n8n_api_key_encrypted,
                        "created_by_admin_id": client.created_by_admin_id,
                        "created_at": client.created_at.isoformat() if client.created_at else None,
                        "updated_at": client.updated_at.isoformat() if client.updated_at else None
                    }
                    clients_data.append(client_dict)
                await self._set_cache(cache_key, clients_data, ttl=180)  # 3 minutes
            
            return clients
    
    async def update_client(
        self,
        db: AsyncSession,
        client_id: str,
        client_data: ClientUpdate,
        admin_user: User
    ) -> Optional[Client]:
        """Update a client with service layer protection"""
        async with self._protected_operation("update_client", admin_user.id):
            result = await db.execute(select(Client).where(Client.id == client_id))
            client = result.scalar_one_or_none()
            
            if not client:
                return None
            
            # Validate updates
            if client_data.name is not None:
                name = client_data.name.strip()
                if not name:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Client name cannot be empty"
                    )
                
                # Check for duplicate names (excluding current client)
                existing = await db.execute(
                    select(Client).where(Client.name == name, Client.id != client_id)
                )
                if existing.scalar_one_or_none():
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Client with this name already exists"
                    )
                
                client.name = name
            
            if client_data.n8n_api_url is not None:
                client.n8n_api_url = client_data.n8n_api_url
            
            await db.commit()
            await db.refresh(client)
            
            # Invalidate caches
            await self._invalidate_cache_pattern(f"clients:get:{client_id}")
            await self._invalidate_cache_pattern("clients:list:*")
            
            logger.info(f"Updated client {client_id} by admin {admin_user.id}")
            return client
    
    async def configure_n8n_api(
        self,
        db: AsyncSession,
        client_id: str,
        n8n_config: ClientN8nConfig,
        admin_user: User
    ) -> Optional[Client]:
        """Configure n8n API settings for a client with service layer protection"""
        async with self._protected_operation("configure_n8n_api", admin_user.id):
            result = await db.execute(select(Client).where(Client.id == client_id))
            client = result.scalar_one_or_none()
            
            if not client:
                return None
            
            # Validate n8n configuration
            if not n8n_config.n8n_api_url or not n8n_config.n8n_api_key:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Both n8n API URL and API key are required"
                )
            
            # Test n8n connection first
            n8n_client = N8nClient()
            n8n_client.configure(n8n_config.n8n_api_url, n8n_config.n8n_api_key)
            
            try:
                # Test the connection with timeout
                connection_healthy = await asyncio.wait_for(
                    n8n_client.health_check(), 
                    timeout=10.0
                )
                
                if not connection_healthy:
                    logger.warning(f"n8n connection test failed for client {client_id}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Failed to connect to n8n instance. Please verify URL and API key."
                    )
                
                # Encrypt and store the API key
                client.n8n_api_key_encrypted = encryption_manager.encrypt(n8n_config.n8n_api_key)
                client.n8n_api_url = n8n_config.n8n_api_url
                
                await db.commit()
                await db.refresh(client)
                
                # Invalidate caches
                await self._invalidate_cache_pattern(f"clients:get:{client_id}")
                await self._invalidate_cache_pattern("clients:list:*")
                
                # Queue background sync task with rate limiting
                try:
                    sync_result = await self._immediate_sync_n8n_data(db, client)
                    logger.info(f"Sync task queued for client {client_id}: {sync_result}")
                except Exception as e:
                    logger.warning(f"Failed to queue sync task for client {client_id}: {e}")
                    # Don't fail the configuration, data can be synced manually later
                
                logger.info(f"Configured n8n API for client {client_id} by admin {admin_user.id}")
                return client
                
            except asyncio.TimeoutError:
                raise HTTPException(
                    status_code=status.HTTP_408_REQUEST_TIMEOUT,
                    detail="n8n connection test timed out"
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error configuring n8n API for client {client_id}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to configure n8n API: {str(e)}"
                )
            finally:
                await n8n_client.close()
    
    @staticmethod
    async def get_n8n_api_key(db: AsyncSession, client_id: str) -> Optional[str]:
        """Get decrypted n8n API key for a client"""
        result = await db.execute(select(Client).where(Client.id == client_id))
        client = result.scalar_one_or_none()
        
        if not client or not client.n8n_api_key_encrypted:
            return None
        
        return encryption_manager.decrypt(client.n8n_api_key_encrypted)
    
    @staticmethod
    def get_n8n_api_key_sync(db: Session, client_id: str) -> Optional[str]:
        """Get decrypted n8n API key for a client (synchronous version for Celery)"""
        client = db.query(Client).filter(Client.id == client_id).first()
        
        if not client or not client.n8n_api_key_encrypted:
            return None
        
        return encryption_manager.decrypt(client.n8n_api_key_encrypted)
    
    @staticmethod
    async def test_n8n_connection(
        n8n_api_url: str,
        n8n_api_key: str
    ) -> Dict[str, Any]:
        """Test n8n API connection without saving configuration"""
        n8n_client = N8nClient()
        
        try:
            n8n_client.configure(n8n_api_url, n8n_api_key)
            
            # Test basic connection
            health_status = await n8n_client.health_check()
            
            if health_status:
                # Get basic instance info
                try:
                    workflows = await n8n_client.get_workflows(limit=1)
                    executions = await n8n_client.get_executions(limit=1)
                    
                    return {
                        "status": "success",
                        "connection_healthy": True,
                        "api_accessible": True,
                        "message": "Successfully connected to n8n instance",
                        "instance_info": {
                            "has_workflows": len(workflows) > 0 if isinstance(workflows, list) else False,
                            "has_executions": len(executions) > 0 if isinstance(executions, list) else False
                        }
                    }
                except Exception as e:
                    return {
                        "status": "warning",
                        "connection_healthy": True,
                        "api_accessible": False,
                        "message": f"Connected but limited API access: {str(e)}",
                        "instance_info": {}
                    }
            else:
                return {
                    "status": "error",
                    "connection_healthy": False,
                    "api_accessible": False,
                    "message": "Failed to connect to n8n instance",
                    "instance_info": {}
                }
        
        except Exception as e:
            logger.error(f"n8n connection test failed: {e}")
            return {
                "status": "error",
                "connection_healthy": False,
                "api_accessible": False,
                "message": f"Connection test failed: {str(e)}",
                "instance_info": {}
            }
        finally:
            await n8n_client.close()
    
    async def delete_client(self, db: AsyncSession, client_id: str, admin_user: User) -> bool:
        """Delete a client with service layer protection"""
        async with self._protected_operation("delete_client", admin_user.id):
            result = await db.execute(select(Client).where(Client.id == client_id))
            client = result.scalar_one_or_none()
            
            if not client:
                return False
            
            # Check if client has associated data that should prevent deletion
            from app.models.workflow import Workflow
            workflow_count = await db.execute(
                select(Workflow).where(Workflow.client_id == client_id).limit(1)
            )
            if workflow_count.scalar_one_or_none():
                logger.warning(f"Attempted to delete client {client_id} with existing workflows")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Cannot delete client with existing workflows. Please remove workflows first."
                )
            
            await db.delete(client)
            await db.commit()
            
            # Invalidate all related caches
            await self._invalidate_cache_pattern(f"clients:get:{client_id}")
            await self._invalidate_cache_pattern("clients:list:*")
            await self._invalidate_cache_pattern(f"workflows:client:{client_id}:*")
            
            logger.info(f"Deleted client {client_id} by admin {admin_user.id}")
            return True
    
    async def _immediate_sync_n8n_data(
        self,
        db: AsyncSession, 
        client: Client
    ) -> Dict[str, Any]:
        """Immediately sync n8n data for a client with rate limiting"""
        # Check if sync is already in progress
        sync_key = f"sync_in_progress:{client.id}"
        if await redis_client.get(sync_key):
            return {
                "status": "skipped",
                "message": "Sync already in progress for this client",
                "client_id": client.id,
                "client_name": client.name
            }
        
        try:
            # Set sync in progress flag (expires in 10 minutes)
            await redis_client.setex(sync_key, 600, "true")
            
            # Rate limit sync operations per client
            sync_rate_key = f"sync_rate_limit:{client.id}"
            if not await self._check_rate_limit(sync_rate_key, limit=5, window=300):  # 5 syncs per 5 minutes
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Sync rate limit exceeded for this client"
                )
            
            # Instead of doing immediate sync which can cause greenlet issues,
            # we'll trigger a Celery task for background processing
            from app.tasks.metrics_tasks import sync_client_metrics
            
            # Trigger async sync via Celery
            task = sync_client_metrics.delay(client.id)
            
            result = {
                "status": "success",
                "message": "Sync task queued successfully",
                "task_id": task.id,
                "client_id": client.id,
                "client_name": client.name
            }
            
            logger.info(f"Sync task queued for client {client.id}: {task.id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to queue sync task for client {client.id}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "client_id": client.id,
                "client_name": client.name
            }
        finally:
            # Clear sync in progress flag
            await redis_client.delete(sync_key)
