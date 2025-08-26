"""Client service"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.client import Client
from app.models.user import User
from app.core.security import encryption_manager
from app.schemas.client import ClientCreate, ClientUpdate, ClientN8nConfig


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
    async def get_client_by_id(db: AsyncSession, client_id: int) -> Optional[Client]:
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
        client_id: int,
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
        client_id: int,
        n8n_config: ClientN8nConfig
    ) -> Optional[Client]:
        """Configure n8n API settings for a client"""
        result = await db.execute(select(Client).where(Client.id == client_id))
        client = result.scalar_one_or_none()
        
        if not client:
            return None
        
        # Encrypt and store the API key
        client.n8n_api_key_encrypted = encryption_manager.encrypt(n8n_config.n8n_api_key)
        client.n8n_api_url = n8n_config.n8n_api_url
        
        await db.commit()
        await db.refresh(client)
        
        return client
    
    @staticmethod
    async def get_n8n_api_key(db: AsyncSession, client_id: int) -> Optional[str]:
        """Get decrypted n8n API key for a client"""
        result = await db.execute(select(Client).where(Client.id == client_id))
        client = result.scalar_one_or_none()
        
        if not client or not client.n8n_api_key_encrypted:
            return None
        
        return encryption_manager.decrypt(client.n8n_api_key_encrypted)
    
    @staticmethod
    def get_n8n_api_key_sync(db: Session, client_id: int) -> Optional[str]:
        """Get decrypted n8n API key for a client (synchronous version for Celery)"""
        client = db.query(Client).filter(Client.id == client_id).first()
        
        if not client or not client.n8n_api_key_encrypted:
            return None
        
        return encryption_manager.decrypt(client.n8n_api_key_encrypted)
    
    @staticmethod
    async def delete_client(db: AsyncSession, client_id: int) -> bool:
        """Delete a client"""
        result = await db.execute(select(Client).where(Client.id == client_id))
        client = result.scalar_one_or_none()
        
        if not client:
            return False
        
        await db.delete(client)
        await db.commit()
        
        return True
