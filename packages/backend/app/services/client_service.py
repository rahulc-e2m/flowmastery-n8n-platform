"""Client service"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status
import logging

from app.models.client import Client
from app.models.user import User
from app.core.security import encryption_manager
from app.schemas.client import ClientCreate, ClientUpdate, ClientN8nConfig
from app.services.n8n.client import N8nClient

logger = logging.getLogger(__name__)


class ClientService:
    """Service for client operations"""
    
    @staticmethod
    async def create_client(
        db: AsyncSession,
        client_data: ClientCreate,
        admin_user: User
    ) -> Client:
        """Create a new client"""
        client = Client(
            name=client_data.name,
            created_by_admin_id=admin_user.id
        )
        
        db.add(client)
        await db.commit()
        await db.refresh(client)
        
        return client
    
    @staticmethod
    async def get_client_by_id(db: AsyncSession, client_id: str) -> Optional[Client]:
        """Get client by ID"""
        result = await db.execute(select(Client).where(Client.id == client_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_all_clients(db: AsyncSession) -> List[Client]:
        """Get all clients"""
        result = await db.execute(select(Client))
        return result.scalars().all()
    
    @staticmethod
    async def update_client(
        db: AsyncSession,
        client_id: str,
        client_data: ClientUpdate
    ) -> Optional[Client]:
        """Update a client"""
        result = await db.execute(select(Client).where(Client.id == client_id))
        client = result.scalar_one_or_none()
        
        if not client:
            return None
        
        if client_data.name is not None:
            client.name = client_data.name
        
        if client_data.n8n_api_url is not None:
            client.n8n_api_url = client_data.n8n_api_url
        
        await db.commit()
        await db.refresh(client)
        
        return client
    
    @staticmethod
    async def configure_n8n_api(
        db: AsyncSession,
        client_id: str,
        n8n_config: ClientN8nConfig
    ) -> Optional[Client]:
        """Configure n8n API settings for a client and immediately fetch data"""
        result = await db.execute(select(Client).where(Client.id == client_id))
        client = result.scalar_one_or_none()
        
        if not client:
            return None
        
        # Test n8n connection first
        n8n_client = N8nClient()
        n8n_client.configure(n8n_config.n8n_api_url, n8n_config.n8n_api_key)
        
        try:
            # Test the connection
            connection_healthy = await n8n_client.health_check()
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
            
            # Immediately fetch n8n data in the background
            try:
                sync_result = await ClientService._immediate_sync_n8n_data(db, client)
                logger.info(f"Immediate sync completed for client {client_id}: {sync_result}")
            except Exception as e:
                logger.warning(f"Immediate sync failed for client {client_id}, will retry via Celery: {e}")
                # Don't fail the configuration, data will be synced later by Celery
            
            return client
            
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
    
    @staticmethod
    async def delete_client(db: AsyncSession, client_id: str) -> bool:
        """Delete a client"""
        result = await db.execute(select(Client).where(Client.id == client_id))
        client = result.scalar_one_or_none()
        
        if not client:
            return False
        
        await db.delete(client)
        await db.commit()
        
        return True
    
    @staticmethod
    async def _immediate_sync_n8n_data(
        db: AsyncSession, 
        client: Client
    ) -> Dict[str, Any]:
        """Immediately sync n8n data for a client after configuration"""
        from app.services.persistent_metrics import PersistentMetricsCollector
        
        try:
            collector = PersistentMetricsCollector()
            
            # Sync workflows first
            api_key = encryption_manager.decrypt(client.n8n_api_key_encrypted)
            workflows_result = await collector._sync_workflows(db, client, api_key)
            
            # Sync recent executions (last 500)
            executions_result = await collector._sync_executions(db, client, api_key, limit=500)
            
            result = {
                "status": "success",
                "workflows_synced": workflows_result,
                "executions_synced": executions_result,
                "client_id": client.id,
                "client_name": client.name
            }
            
            logger.info(f"Immediate sync successful for client {client.id}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Immediate sync failed for client {client.id}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "client_id": client.id,
                "client_name": client.name
            }
