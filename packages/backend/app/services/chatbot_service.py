"""Chatbot service"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_

from ..models import Chatbot, Client, User
from ..schemas.chatbot import ChatbotCreate, ChatbotUpdate, ChatbotResponse, ChatbotListResponse
from ..core.user_roles import RolePermissions


class ChatbotService:
    """Service for managing chatbots"""
    
    @staticmethod
    async def get_all_chatbots(db: AsyncSession) -> ChatbotListResponse:
        """Get all chatbots (admin only)"""
        stmt = (
            select(Chatbot)
            .options(selectinload(Chatbot.client))
            .order_by(Chatbot.created_at.desc())
        )
        result = await db.execute(stmt)
        chatbots = result.scalars().all()
        
        chatbot_responses = []
        for chatbot in chatbots:
            chatbot_responses.append(ChatbotResponse(
                id=chatbot.id,
                name=chatbot.name,
                description=chatbot.description,
                webhook_url=chatbot.webhook_url,
                is_active=chatbot.is_active,
                client_id=chatbot.client_id,
                client_name=chatbot.client.name,
                created_by_user_id=chatbot.created_by_user_id,
                created_at=chatbot.created_at,
                updated_at=chatbot.updated_at
            ))
        
        return ChatbotListResponse(
            chatbots=chatbot_responses,
            total=len(chatbot_responses)
        )
    
    @staticmethod
    async def get_user_chatbots(db: AsyncSession, user: User) -> ChatbotListResponse:
        """Get chatbots for a specific user's client"""
        if not user.client_id:
            return ChatbotListResponse(chatbots=[], total=0)
        
        stmt = (
            select(Chatbot)
            .options(selectinload(Chatbot.client))
            .where(Chatbot.client_id == user.client_id)
            .order_by(Chatbot.created_at.desc())
        )
        result = await db.execute(stmt)
        chatbots = result.scalars().all()
        
        chatbot_responses = []
        for chatbot in chatbots:
            chatbot_responses.append(ChatbotResponse(
                id=chatbot.id,
                name=chatbot.name,
                description=chatbot.description,
                webhook_url=chatbot.webhook_url,
                is_active=chatbot.is_active,
                client_id=chatbot.client_id,
                client_name=chatbot.client.name,
                created_by_user_id=chatbot.created_by_user_id,
                created_at=chatbot.created_at,
                updated_at=chatbot.updated_at
            ))
        
        return ChatbotListResponse(
            chatbots=chatbot_responses,
            total=len(chatbot_responses)
        )
    
    @staticmethod
    async def get_chatbot_by_id(db: AsyncSession, chatbot_id: str, user: User) -> Optional[ChatbotResponse]:
        """Get a specific chatbot by ID"""
        stmt = select(Chatbot).options(selectinload(Chatbot.client))
        
        # If user is not admin, filter by their client
        if not RolePermissions.is_admin(user.role):
            if not user.client_id:
                return None
            stmt = stmt.where(Chatbot.client_id == user.client_id)
        
        stmt = stmt.where(Chatbot.id == chatbot_id)
        result = await db.execute(stmt)
        chatbot = result.scalars().first()
        
        if not chatbot:
            return None
        
        return ChatbotResponse(
            id=chatbot.id,
            name=chatbot.name,
            description=chatbot.description,
            webhook_url=chatbot.webhook_url,
            is_active=chatbot.is_active,
            client_id=chatbot.client_id,
            client_name=chatbot.client.name,
            created_by_user_id=chatbot.created_by_user_id,
            created_at=chatbot.created_at,
            updated_at=chatbot.updated_at
        )
    
    @staticmethod
    async def create_chatbot(db: AsyncSession, chatbot_data: ChatbotCreate, user: User) -> ChatbotResponse:
        """Create a new chatbot"""
        # Verify the client exists and user has access
        stmt = select(Client).where(Client.id == chatbot_data.client_id)
        result = await db.execute(stmt)
        client = result.scalars().first()
        if not client:
            raise ValueError("Client not found")
        
        # If user is not admin, they can only create chatbots for their own client
        if not RolePermissions.is_admin(user.role) and user.client_id != chatbot_data.client_id:
            raise ValueError("You can only create chatbots for your own client")
        
        # Create the chatbot
        chatbot = Chatbot(
            name=chatbot_data.name,
            description=chatbot_data.description,
            webhook_url=chatbot_data.webhook_url,
            is_active=chatbot_data.is_active,
            client_id=chatbot_data.client_id,
            created_by_user_id=user.id
        )
        
        db.add(chatbot)
        await db.commit()
        await db.refresh(chatbot)
        
        # Load the client relationship
        await db.refresh(chatbot, ['client'])
        
        return ChatbotResponse(
            id=chatbot.id,
            name=chatbot.name,
            description=chatbot.description,
            webhook_url=chatbot.webhook_url,
            is_active=chatbot.is_active,
            client_id=chatbot.client_id,
            client_name=chatbot.client.name,
            created_by_user_id=chatbot.created_by_user_id,
            created_at=chatbot.created_at,
            updated_at=chatbot.updated_at
        )
    
    @staticmethod
    async def update_chatbot(db: AsyncSession, chatbot_id: str, chatbot_data: ChatbotUpdate, user: User) -> Optional[ChatbotResponse]:
        """Update an existing chatbot"""
        stmt = select(Chatbot)
        
        # If user is not admin, filter by their client
        if not RolePermissions.is_admin(user.role):
            if not user.client_id:
                return None
            stmt = stmt.where(Chatbot.client_id == user.client_id)
        
        stmt = stmt.where(Chatbot.id == chatbot_id)
        result = await db.execute(stmt)
        chatbot = result.scalars().first()
        
        if not chatbot:
            return None
        
        # If changing client_id, verify the new client exists and user has access
        if chatbot_data.client_id and chatbot_data.client_id != chatbot.client_id:
            stmt = select(Client).where(Client.id == chatbot_data.client_id)
            result = await db.execute(stmt)
            client = result.scalars().first()
            if not client:
                raise ValueError("Client not found")
            
            # If user is not admin, they can only move chatbots to their own client
            if not RolePermissions.is_admin(user.role) and user.client_id != chatbot_data.client_id:
                raise ValueError("You can only assign chatbots to your own client")
        
        # Update fields
        update_data = chatbot_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(chatbot, field, value)
        
        await db.commit()
        await db.refresh(chatbot)
        
        # Load the client relationship
        await db.refresh(chatbot, ['client'])
        
        return ChatbotResponse(
            id=chatbot.id,
            name=chatbot.name,
            description=chatbot.description,
            webhook_url=chatbot.webhook_url,
            is_active=chatbot.is_active,
            client_id=chatbot.client_id,
            client_name=chatbot.client.name,
            created_by_user_id=chatbot.created_by_user_id,
            created_at=chatbot.created_at,
            updated_at=chatbot.updated_at
        )
    
    @staticmethod
    async def delete_chatbot(db: AsyncSession, chatbot_id: str, user: User) -> bool:
        """Delete a chatbot"""
        stmt = select(Chatbot)
        
        # If user is not admin, filter by their client
        if not RolePermissions.is_admin(user.role):
            if not user.client_id:
                return False
            stmt = stmt.where(Chatbot.client_id == user.client_id)
        
        stmt = stmt.where(Chatbot.id == chatbot_id)
        result = await db.execute(stmt)
        chatbot = result.scalars().first()
        
        if not chatbot:
            return False
        
        await db.delete(chatbot)
        await db.commit()
        return True
