"""Authentication endpoints"""

from datetime import timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.invitation import Invitation
from app.core.dependencies import get_current_user, get_current_admin_user
from app.core.auth import create_access_token
from app.services.auth_service import AuthService
from app.schemas.auth import (
    UserLogin, 
    Token, 
    InvitationCreate, 
    InvitationResponse,
    InvitationAccept,
    UserResponse,
    UserProfileUpdate
)
from app.config import settings

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    user_credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return JWT token"""
    user = await AuthService.authenticate_user(
        db, user_credentials.email, user_credentials.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return UserResponse.model_validate(current_user)


@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user's profile information"""
    # Update user fields
    if profile_data.first_name is not None:
        current_user.first_name = profile_data.first_name
    if profile_data.last_name is not None:
        current_user.last_name = profile_data.last_name
    
    await db.commit()
    await db.refresh(current_user)
    
    return UserResponse.model_validate(current_user)


@router.post("/invitations", response_model=InvitationResponse)
async def create_invitation(
    invitation_data: InvitationCreate,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Create a new invitation (admin only)"""
    invitation = await AuthService.create_invitation(db, invitation_data, admin_user)
    return InvitationResponse.model_validate(invitation)


@router.get("/invitations", response_model=List[InvitationResponse])
async def list_invitations(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """List all invitations (admin only)"""
    result = await db.execute(select(Invitation).order_by(Invitation.created_at.desc()))
    invitations = result.scalars().all()
    return [InvitationResponse.model_validate(inv) for inv in invitations]


@router.get("/invitations/{invitation_id}/link")
async def get_invitation_link(
    invitation_id: str,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Get invitation link by invitation ID (admin only)"""
    result = await db.execute(select(Invitation).where(Invitation.id == invitation_id))
    invitation = result.scalar_one_or_none()
    
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )
    
    if invitation.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation is not pending"
        )
    
    if invitation.is_expired:
        invitation.status = "expired"
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation has expired"
        )
    
    # Return the invitation link pointing to homepage with token
    invitation_link = f"{settings.FRONTEND_URL}/?token={invitation.token}"
    
    return {
        "invitation_link": invitation_link,
        "token": invitation.token
    }


@router.get("/invitations/{token}")
async def get_invitation_details(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """Get invitation details by token (for invitation acceptance page)"""
    invitation = await AuthService.get_invitation_by_token(db, token)
    
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
    
    return {
        "email": invitation.email,
        "role": invitation.role,
        "expires_at": invitation.expiry_date
    }


@router.post("/invitations/accept", response_model=Token)
async def accept_invitation(
    accept_data: InvitationAccept,
    db: AsyncSession = Depends(get_db)
):
    """Accept an invitation and create user account"""
    user = await AuthService.accept_invitation(db, accept_data)
    
    # Create access token for the new user
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.delete("/invitations/{invitation_id}")
async def revoke_invitation(
    invitation_id: str,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Revoke a pending invitation (admin only)"""
    invitation = await AuthService.revoke_invitation(db, invitation_id)
    
    return {
        "message": f"Invitation for {invitation.email} has been revoked",
        "invitation_id": invitation_id,
        "email": invitation.email
    }