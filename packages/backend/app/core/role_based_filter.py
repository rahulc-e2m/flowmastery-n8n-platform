"""Role-based data filtering utilities for API reorganization"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status, Depends

from app.models.user import User
from app.models.client import Client
from app.models.workflow import Workflow
from app.models.chatbot import Chatbot
from app.core.user_roles import UserRole, RolePermissions
from app.database import get_db


class RoleBasedDataFilter:
    """Utility class for filtering data based on user roles and permissions"""
    
    @staticmethod
    async def filter_clients_by_role(
        user: User, 
        db: AsyncSession,
        client_id: Optional[str] = None
    ) -> List[Client]:
        """Return clients based on user role and optional client_id filter"""
        
        if RolePermissions.is_admin(user.role):
            # Admins can see all clients or specific client if requested
            query = select(Client)
            if client_id:
                query = query.where(Client.id == client_id)
            result = await db.execute(query)
            return result.scalars().all()
        
        elif RolePermissions.is_client(user.role):
            # Clients can only see their own client
            if not user.client_id:
                return []
            
            # If specific client_id requested, verify access
            if client_id and client_id != user.client_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this client's data"
                )
            
            result = await db.execute(
                select(Client).where(Client.id == user.client_id)
            )
            client = result.scalar_one_or_none()
            return [client] if client else []
        
        else:
            # Unknown role
            return []
    
    @staticmethod
    async def get_accessible_client_ids(
        user: User,
        db: AsyncSession,
        requested_client_id: Optional[str] = None
    ) -> List[str]:
        """Get list of client IDs the user can access"""
        
        if RolePermissions.is_admin(user.role):
            if requested_client_id:
                # Verify the requested client exists
                result = await db.execute(
                    select(Client.id).where(Client.id == requested_client_id)
                )
                if result.scalar_one_or_none():
                    return [requested_client_id]
                else:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Client not found"
                    )
            else:
                # Return all client IDs
                result = await db.execute(select(Client.id))
                return [row[0] for row in result.fetchall()]
        
        elif RolePermissions.is_client(user.role):
            if not user.client_id:
                return []
            
            # If specific client requested, verify it's their own
            if requested_client_id and requested_client_id != user.client_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this client's data"
                )
            
            return [user.client_id]
        
        else:
            return []
    
    @staticmethod
    async def verify_resource_access(
        user: User,
        resource_type: str,
        resource_id: str,
        db: AsyncSession
    ) -> bool:
        """Verify user can access specific resource"""
        
        if RolePermissions.is_admin(user.role):
            return True
        
        if not RolePermissions.is_client(user.role) or not user.client_id:
            return False
        
        # Check resource ownership based on type
        if resource_type == "workflow":
            result = await db.execute(
                select(Workflow.client_id).where(Workflow.id == resource_id)
            )
            workflow_client_id = result.scalar_one_or_none()
            return workflow_client_id == user.client_id
        
        elif resource_type == "chatbot":
            result = await db.execute(
                select(Chatbot.client_id).where(Chatbot.id == resource_id)
            )
            chatbot_client_id = result.scalar_one_or_none()
            return chatbot_client_id == user.client_id
        
        elif resource_type == "client":
            return resource_id == user.client_id
        
        else:
            # Unknown resource type
            return False
    
    @staticmethod
    def get_admin_or_client_user():
        """Dependency factory for endpoints that allow both admin and client access"""
        from app.core.dependencies import get_current_user
        return get_current_user(required_roles=[UserRole.ADMIN, UserRole.CLIENT])
    
    @staticmethod
    def verify_workflow_access(workflow_id: str):
        """Dependency factory to verify workflow access"""
        async def _verify_workflow_access(
            current_user: User = Depends(RoleBasedDataFilter.get_admin_or_client_user()),
            db: AsyncSession = Depends(get_db)
        ) -> User:
            if not await RoleBasedDataFilter.verify_resource_access(
                current_user, "workflow", workflow_id, db
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this workflow"
                )
            return current_user
        
        return _verify_workflow_access
    
    @staticmethod
    def verify_chatbot_access(chatbot_id: str):
        """Dependency factory to verify chatbot access"""
        async def _verify_chatbot_access(
            current_user: User = Depends(RoleBasedDataFilter.get_admin_or_client_user()),
            db: AsyncSession = Depends(get_db)
        ) -> User:
            if not await RoleBasedDataFilter.verify_resource_access(
                current_user, "chatbot", chatbot_id, db
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this chatbot"
                )
            return current_user
        
        return _verify_chatbot_access