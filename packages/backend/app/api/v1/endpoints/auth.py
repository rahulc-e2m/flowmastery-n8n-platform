"""Authentication endpoints with cookie support"""

from datetime import timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.models.user import User
from app.models.invitation import Invitation
from app.core.dependencies import get_current_user, get_current_admin_user, get_optional_user
from app.core.auth import create_access_token, create_refresh_token, verify_token
from app.core.rate_limiting import get_user_identifier, RATE_LIMITS
from app.services.auth_service import AuthService
from app.schemas.auth import (
    UserLogin, 
    Token, 
    RefreshTokenRequest,
    TokenRefreshResponse,
    InvitationCreate, 
    InvitationResponse,
    InvitationAccept,
    UserResponse,
    UserProfileUpdate
)
from app.config import settings
from app.core.decorators import validate_input, sanitize_response

router = APIRouter()

# Initialize rate limiter
limiter = Limiter(key_func=get_user_identifier)


@router.post("/login", response_model=Token)
@limiter.limit(RATE_LIMITS["auth_login"])
@validate_input(validate_emails=True, max_string_length=255)
@sanitize_response()
async def login(
    request: Request,
    response: Response,
    user_credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return JWT token via httpOnly cookies"""
    user = await AuthService.authenticate_user(
        db, user_credentials.email, user_credentials.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
    
    access_token = create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(
        data=token_data,
        expires_delta=refresh_token_expires
    )
    
    # Set httpOnly cookies for tokens
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=settings.ENVIRONMENT.lower() == "production",
        samesite="lax"
    )
    
    response.set_cookie(
        key="refresh_token", 
        value=refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=settings.ENVIRONMENT.lower() == "production",
        samesite="lax"
    )
    
    return Token(
        access_token="",  # Don't return token in response body for security
        refresh_token="", # Don't return token in response body for security
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
        user=UserResponse.model_validate(user)
    )


@router.post("/refresh", response_model=TokenRefreshResponse)
@limiter.limit(RATE_LIMITS["auth_refresh"])
@sanitize_response()
async def refresh_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token from cookie"""
    # Get refresh token from cookie
    refresh_token_value = request.cookies.get("refresh_token")
    
    if not refresh_token_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token found",
        )
    
    try:
        # Verify refresh token
        payload = verify_token(refresh_token_value, token_type="refresh")
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
        
        # Get user from database to ensure they still exist and are active
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )
        
        # Create new tokens
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
        
        new_access_token = create_access_token(
            data=token_data,
            expires_delta=access_token_expires
        )
        
        new_refresh_token = create_refresh_token(
            data=token_data,
            expires_delta=refresh_token_expires
        )
        
        # Set new httpOnly cookies
        response.set_cookie(
            key="access_token",
            value=new_access_token,
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            httponly=True,
            secure=settings.ENVIRONMENT.lower() == "production",
            samesite="lax"
        )
        
        response.set_cookie(
            key="refresh_token", 
            value=new_refresh_token,
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            httponly=True,
            secure=settings.ENVIRONMENT.lower() == "production",
            samesite="lax"
        )
        
        return TokenRefreshResponse(
            access_token="",  # Don't return token in response body
            refresh_token="", # Don't return token in response body
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
        )
        
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )


@router.post("/logout")
async def logout(response: Response):
    """Logout user by clearing cookies"""
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_optional_user)
):
    """Get current user information"""
    if current_user:
        return UserResponse.model_validate(current_user)
    return None


@router.get("/status")
async def get_auth_status(
    current_user: User = Depends(get_optional_user)
):
    """Check authentication status without throwing errors"""
    return {
        "authenticated": current_user is not None,
        "user": UserResponse.model_validate(current_user) if current_user else None
    }


@router.put("/profile", response_model=UserResponse)
@validate_input(max_string_length=255)
@sanitize_response()
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
@limiter.limit(RATE_LIMITS["invitation_create"])
@validate_input(validate_emails=True, max_string_length=500)
@sanitize_response()
async def create_invitation(
    request: Request,
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
@validate_input(validate_emails=True, max_string_length=500)
@sanitize_response()
async def accept_invitation(
    accept_data: InvitationAccept,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """Accept an invitation and create user account"""
    user = await AuthService.accept_invitation(db, accept_data)
    
    # Create tokens for the new user
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
    
    access_token = create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(
        data=token_data,
        expires_delta=refresh_token_expires
    )
    
    # Set httpOnly cookies for tokens
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=settings.ENVIRONMENT.lower() == "production",
        samesite="lax"
    )
    
    response.set_cookie(
        key="refresh_token", 
        value=refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=settings.ENVIRONMENT.lower() == "production",
        samesite="lax"
    )
    
    return Token(
        access_token="",  # Don't return token in response body
        refresh_token="", # Don't return token in response body
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
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