"""Authentication service"""

from datetime import datetime, timedelta, timezone
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.user import User
from app.models.client import Client
from app.models.invitation import Invitation
from app.core.auth import verify_password, get_password_hash, create_access_token
from app.core.security import generate_invitation_token, validate_invitation_token, is_invitation_token_expired
from app.schemas.auth import UserCreate, UserLogin, InvitationCreate, InvitationAccept, UserProfileUpdate
from app.services.email_service import send_invitation_email
from app.config import settings
from app.core.service_layer import OperationContext, OperationType, OperationResult, BaseService
from app.core.auth import verify_token


class AuthService(BaseService):
    """Service for authentication operations"""
    
    def __init__(self):
        super().__init__()
        self._service_name = "auth_service"
    
    @property
    def service_name(self) -> str:
        return self._service_name
    
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
        # First validate the token timestamp
        try:
            token_payload = validate_invitation_token(accept_data.token, max_age_hours=settings.INVITATION_TOKEN_EXPIRE_HOURS)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid or expired invitation token: {str(e)}"
            )
        
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
        
        # Check both token timestamp and database expiry
        if invitation.is_expired or is_invitation_token_expired(accept_data.token, max_age_hours=settings.INVITATION_TOKEN_EXPIRE_HOURS):
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
        """Get invitation by token with timestamp validation"""
        # First validate the token timestamp
        try:
            validate_invitation_token(token, max_age_hours=settings.INVITATION_TOKEN_EXPIRE_HOURS)
        except ValueError:
            # Token is invalid or expired based on timestamp
            return None
        
        result = await db.execute(select(Invitation).where(Invitation.token == token))
        invitation = result.scalar_one_or_none()
        
        # Double-check expiration at database level too
        if invitation and (invitation.is_expired or is_invitation_token_expired(token, max_age_hours=settings.INVITATION_TOKEN_EXPIRE_HOURS)):
            # Mark as expired in database if not already
            if invitation.status == "pending":
                invitation.status = "expired"
                await db.commit()
            return None
            
        return invitation
    
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
    
    async def update_user_profile(
        self,
        db: AsyncSession,
        user: User,
        profile_data: UserProfileUpdate,
        context: OperationContext
    ) -> OperationResult[User]:
        """Update user profile with service layer protection"""
        context.operation_type = OperationType.UPDATE
        
        async def _update_operation():
            # Validate input
            if not profile_data.first_name and not profile_data.last_name:
                raise ValueError("At least one field must be provided for update")
            
            # Update user fields
            if profile_data.first_name is not None:
                user.first_name = profile_data.first_name
            if profile_data.last_name is not None:
                user.last_name = profile_data.last_name
            
            # Set updated timestamp
            user.updated_at = datetime.now(timezone.utc)
            
            await db.commit()
            await db.refresh(user)
            
            # Invalidate user cache if needed
            await self._invalidate_cache(f"user:{user.id}")
            
            return user
        
        return await self.execute_operation(_update_operation, context)
    
    async def refresh_user_token(
        self,
        db: AsyncSession,
        refresh_token: str,
        context: OperationContext
    ) -> OperationResult[User]:
        """Refresh user token with service layer protection and validation"""
        context.operation_type = OperationType.READ
        
        async def _refresh_operation():
            # Verify refresh token
            payload = verify_token(refresh_token, token_type="refresh")
            user_id = payload.get("sub")
            
            if not user_id:
                raise ValueError("Invalid refresh token")
            
            # Try cache first
            cache_key = f"user:{user_id}"
            cached_user = await self._get_from_cache(cache_key)
            
            if cached_user:
                # Validate cached user is still active
                if cached_user.get('is_active'):
                    return User(**cached_user)
            
            # Get user from database
            async with self._get_db_session() as db_session:
                result = await db_session.execute(select(User).where(User.id == user_id))
                user = result.scalar_one_or_none()
                
                if not user or not user.is_active:
                    raise ValueError("User not found or inactive")
                
                # Cache the user for future requests
                user_dict = {
                    'id': user.id,
                    'email': user.email,
                    'role': user.role,
                    'is_active': user.is_active,
                    'client_id': user.client_id
                }
                await self._set_cache(cache_key, user_dict, ttl=300)  # 5 minutes
                
                return user
        
        return await self.execute_operation(_refresh_operation, context)
    
    async def list_invitations(
        self,
        db: AsyncSession,
        context: OperationContext,
        use_cache: bool = True
    ) -> OperationResult[List[Invitation]]:
        """List all invitations with service layer protection"""
        context.operation_type = OperationType.READ
        
        async def _list_operation():
            cache_key = "invitations:list"
            
            # Try cache first
            if use_cache:
                cached_result = await self._get_from_cache(cache_key)
                if cached_result is not None:
                    return [Invitation(**inv) for inv in cached_result]
            
            # Get from database
            async with self._get_db_session() as db_session:
                result = await db_session.execute(
                    select(Invitation).order_by(Invitation.created_at.desc())
                )
                invitations = result.scalars().all()
                
                # Cache the result
                if use_cache:
                    invitations_dict = [
                        {
                            'id': inv.id,
                            'email': inv.email,
                            'role': inv.role,
                            'status': inv.status,
                            'created_at': inv.created_at.isoformat() if inv.created_at else None,
                            'client_id': inv.client_id
                        }
                        for inv in invitations
                    ]
                    await self._set_cache(cache_key, invitations_dict, ttl=180)  # 3 minutes
                
                return list(invitations)
        
        return await self.execute_operation(_list_operation, context)
    
    async def get_invitation_by_id(
        self,
        db: AsyncSession,
        invitation_id: str,
        context: OperationContext,
        use_cache: bool = True
    ) -> OperationResult[Optional[Invitation]]:
        """Get invitation by ID with service layer protection"""
        context.operation_type = OperationType.READ
        
        async def _get_operation():
            cache_key = f"invitation:{invitation_id}"
            
            # Try cache first
            if use_cache:
                cached_result = await self._get_from_cache(cache_key)
                if cached_result is not None:
                    return Invitation(**cached_result) if cached_result else None
            
            # Get from database
            async with self._get_db_session() as db_session:
                result = await db_session.execute(
                    select(Invitation).where(Invitation.id == invitation_id)
                )
                invitation = result.scalar_one_or_none()
                
                # Cache the result
                if use_cache:
                    if invitation:
                        invitation_dict = {
                            'id': invitation.id,
                            'email': invitation.email,
                            'role': invitation.role,
                            'status': invitation.status,
                            'token': invitation.token,
                            'created_at': invitation.created_at.isoformat() if invitation.created_at else None,
                            'expiry_date': invitation.expiry_date.isoformat() if invitation.expiry_date else None,
                            'client_id': invitation.client_id,
                            'is_expired': invitation.is_expired
                        }
                        await self._set_cache(cache_key, invitation_dict, ttl=300)
                    else:
                        await self._set_cache(cache_key, None, ttl=60)  # Cache miss for 1 minute
                
                return invitation
        
        return await self.execute_operation(_get_operation, context)
    
    async def update_invitation_status(
        self,
        db: AsyncSession,
        invitation_id: str,
        status: str,
        context: OperationContext
    ) -> OperationResult[bool]:
        """Update invitation status with service layer protection"""
        context.operation_type = OperationType.UPDATE
        
        async def _update_status_operation():
            async with self._get_db_session() as db_session:
                result = await db_session.execute(
                    select(Invitation).where(Invitation.id == invitation_id)
                )
                invitation = result.scalar_one_or_none()
                
                if not invitation:
                    raise ValueError("Invitation not found")
                
                invitation.status = status
                await db_session.commit()
                
                # Invalidate cache
                await self._invalidate_cache(f"invitation:{invitation_id}")
                await self._invalidate_cache("invitations:list")
                
                return True
        
        return await self.execute_operation(_update_status_operation, context)
