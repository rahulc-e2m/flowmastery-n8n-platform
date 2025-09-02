"""Authentication endpoints with cookie support and service layer protection"""

import asyncio
import logging
from datetime import datetime, timedelta
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
from app.services.cache.redis import redis_client

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_user_identifier)


class AuthServiceMixin:
    """Service layer mixin for authentication operations"""
    
    @staticmethod
    async def _check_auth_rate_limit(user_identifier: str, operation: str, limit: int = 10, window: int = 300) -> bool:
        """Check rate limit for auth operations (stricter limits for security)"""
        try:
            current_time = int(datetime.utcnow().timestamp())
            window_start = current_time - window
            rate_limit_key = f"rate_limit:auth:{operation}:{user_identifier}"
            
            pipe = redis_client.pipeline()
            pipe.zremrangebyscore(rate_limit_key, 0, window_start)
            pipe.zcard(rate_limit_key)
            pipe.zadd(rate_limit_key, {str(current_time): current_time})
            pipe.expire(rate_limit_key, window)
            
            results = await pipe.execute()
            current_requests = results[1]
            
            return current_requests < limit
        except Exception as e:
            logger.warning(f"Auth rate limiter error: {e}")
            return True  # Fail open but log the issue
    
    @staticmethod
    async def _log_auth_event(event_type: str, user_id: str = None, email: str = None, success: bool = True, details: str = None):
        """Log authentication events for security monitoring"""
        try:
            log_data = {
                "event_type": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "email": email,
                "success": success,
                "details": details
            }
            
            # Store in Redis for security monitoring (expire after 30 days)
            auth_log_key = f"auth_log:{datetime.utcnow().strftime('%Y-%m-%d')}:{event_type}:{user_id or email or 'unknown'}"
            await redis_client.setex(auth_log_key, 30 * 24 * 60 * 60, str(log_data))
            
            # Also log to application logs
            if success:
                logger.info(f"Auth event: {event_type} - {email or user_id} - {details or 'success'}")
            else:
                logger.warning(f"Auth event failed: {event_type} - {email or user_id} - {details or 'failed'}")
                
        except Exception as e:
            logger.error(f"Failed to log auth event: {e}")
    
    @staticmethod
    async def _check_brute_force_protection(identifier: str) -> bool:
        """Check for brute force attacks"""
        try:
            # Check failed login attempts in the last hour
            failed_key = f"auth_failures:{identifier}"
            failed_count = await redis_client.get(failed_key)
            
            if failed_count and int(failed_count) >= 5:  # 5 failed attempts
                return False
            
            return True
        except Exception as e:
            logger.warning(f"Brute force check error: {e}")
            return True  # Fail open
    
    @staticmethod
    async def _record_auth_failure(identifier: str):
        """Record authentication failure for brute force protection"""
        try:
            failed_key = f"auth_failures:{identifier}"
            pipe = redis_client.pipeline()
            pipe.incr(failed_key)
            pipe.expire(failed_key, 3600)  # 1 hour
            await pipe.execute()
        except Exception as e:
            logger.warning(f"Failed to record auth failure: {e}")
    
    @staticmethod
    async def _clear_auth_failures(identifier: str):
        """Clear authentication failures on successful login"""
        try:
            failed_key = f"auth_failures:{identifier}"
            await redis_client.delete(failed_key)
        except Exception as e:
            logger.warning(f"Failed to clear auth failures: {e}")


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
    """Authenticate user and return JWT token via httpOnly cookies with service layer protection"""
    client_ip = request.client.host if request.client else "unknown"
    user_identifier = f"{user_credentials.email}:{client_ip}"
    
    # Enhanced rate limiting for login attempts
    if not await AuthServiceMixin._check_auth_rate_limit(user_identifier, "login", limit=5, window=300):
        await AuthServiceMixin._log_auth_event("login_rate_limited", email=user_credentials.email, success=False, details=f"IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later."
        )
    
    # Brute force protection
    if not await AuthServiceMixin._check_brute_force_protection(user_identifier):
        await AuthServiceMixin._log_auth_event("login_brute_force_blocked", email=user_credentials.email, success=False, details=f"IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Account temporarily locked due to multiple failed attempts"
        )
    
    try:
        user = await AuthService.authenticate_user(
            db, user_credentials.email, user_credentials.password
        )
        
        if not user:
            await AuthServiceMixin._record_auth_failure(user_identifier)
            await AuthServiceMixin._log_auth_event("login_failed", email=user_credentials.email, success=False, details="Invalid credentials")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Clear any previous failures on successful login
        await AuthServiceMixin._clear_auth_failures(user_identifier)
        await AuthServiceMixin._log_auth_event("login_success", user_id=user.id, email=user.email, success=True, details=f"IP: {client_ip}")
        
    except HTTPException:
        raise
    except Exception as e:
        await AuthServiceMixin._log_auth_event("login_error", email=user_credentials.email, success=False, details=str(e))
        logger.error(f"Login error for {user_credentials.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service temporarily unavailable"
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
    """Create a new invitation (admin only) with service layer protection"""
    # Rate limiting for invitation creation
    if not await AuthServiceMixin._check_auth_rate_limit(admin_user.id, "create_invitation", limit=10, window=300):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many invitation creation attempts"
        )
    
    try:
        invitation = await AuthService.create_invitation(db, invitation_data, admin_user)
        await AuthServiceMixin._log_auth_event("invitation_created", user_id=admin_user.id, email=invitation_data.email, success=True)
        return InvitationResponse.model_validate(invitation)
    except Exception as e:
        await AuthServiceMixin._log_auth_event("invitation_creation_failed", user_id=admin_user.id, email=invitation_data.email, success=False, details=str(e))
        logger.error(f"Invitation creation failed: {e}")
        raise


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