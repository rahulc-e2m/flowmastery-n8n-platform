"""Authentication service"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.user import User
from app.models.client import Client
from app.models.invitation import Invitation
from app.core.auth import verify_password, get_password_hash, create_access_token
from app.core.security import generate_invitation_token
from app.schemas.auth import UserCreate, UserLogin, InvitationCreate, InvitationAccept
from app.services.email_service import send_invitation_email


class AuthService:
    """Service for authentication operations"""
    
    @staticmethod
    async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
        """Authenticate a user with email and password"""
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user or not verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            return None
        
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        await db.commit()
        
        return user
    
    @staticmethod
    async def create_user_from_invitation(
        db: AsyncSession, 
        invitation: Invitation, 
        password: str
    ) -> User:
        """Create a user from an accepted invitation"""
        # Create user
        user = User(
            email=invitation.email,
            hashed_password=get_password_hash(password),
            role=invitation.role,
            client_id=invitation.client_id,
            created_by_admin_id=invitation.invited_by_admin_id
        )
        
        db.add(user)
        await db.flush()  # Get the user ID
        
        # Update invitation
        invitation.status = "accepted"
        invitation.accepted_user_id = user.id
        invitation.accepted_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(user)
        
        return user
    
    @staticmethod
    async def create_invitation(
        db: AsyncSession,
        invitation_data: InvitationCreate,
        admin_user: User
    ) -> Invitation:
        """Create a new invitation"""
        # Check if user already exists
        result = await db.execute(select(User).where(User.email == invitation_data.email))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Check for pending invitations
        result = await db.execute(
            select(Invitation).where(
                Invitation.email == invitation_data.email,
                Invitation.status == "pending"
            )
        )
        existing_invitation = result.scalar_one_or_none()
        
        if existing_invitation and not existing_invitation.is_expired:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pending invitation already exists for this email"
            )
        
        # For client invitations, validate client_id
        if invitation_data.role == "client" and invitation_data.client_id:
            result = await db.execute(select(Client).where(Client.id == invitation_data.client_id))
            client = result.scalar_one_or_none()
            if not client:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Client not found"
                )
        
        # Create invitation
        invitation = Invitation(
            email=invitation_data.email,
            role=invitation_data.role,
            token=generate_invitation_token(),
            client_id=invitation_data.client_id,
            invited_by_admin_id=admin_user.id
        )
        
        db.add(invitation)
        await db.commit()
        await db.refresh(invitation)
        
        # Send invitation email
        await send_invitation_email(invitation)
        
        return invitation
    
    @staticmethod
    async def accept_invitation(
        db: AsyncSession,
        accept_data: InvitationAccept
    ) -> User:
        """Accept an invitation and create user account"""
        # Find invitation by token
        result = await db.execute(
            select(Invitation).where(Invitation.token == accept_data.token)
        )
        invitation = result.scalar_one_or_none()
        
        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid invitation token"
            )
        
        if invitation.status != "pending":
            if invitation.status == "revoked":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This invitation has been revoked"
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation has already been used or expired"
            )
        
        if invitation.is_expired:
            invitation.status = "expired"
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation has expired"
            )
        
        # Create user
        user = await AuthService.create_user_from_invitation(
            db, invitation, accept_data.password
        )
        
        return user
    
    @staticmethod
    async def get_invitation_by_token(db: AsyncSession, token: str) -> Optional[Invitation]:
        """Get invitation by token"""
        result = await db.execute(select(Invitation).where(Invitation.token == token))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def revoke_invitation(db: AsyncSession, invitation_id: str) -> Invitation:
        """Revoke a pending invitation"""
        # Find invitation by ID
        result = await db.execute(
            select(Invitation).where(Invitation.id == invitation_id)
        )
        invitation = result.scalar_one_or_none()
        
        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found"
            )
        
        if invitation.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot revoke invitation with status '{invitation.status}'. Only pending invitations can be revoked."
            )
        
        # Update invitation status to revoked
        invitation.status = "revoked"
        await db.commit()
        await db.refresh(invitation)
        
        return invitation