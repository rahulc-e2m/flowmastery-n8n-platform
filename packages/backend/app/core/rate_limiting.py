"""Rate limiting utilities and configurations"""

from typing import Optional
from fastapi import Request
from slowapi.util import get_remote_address
from app.config import settings
import re


def get_user_identifier(request: Request) -> str:
    """
    Get unique identifier for rate limiting.
    Uses user ID if authenticated, otherwise falls back to IP address.
    """
    # Try to get user ID from JWT token in Authorization header
    authorization = request.headers.get("Authorization")
    if authorization and authorization.startswith("Bearer "):
        try:
            # Import here to avoid circular imports
            from app.core.auth import decode_access_token
            token = authorization.split(" ")[1]
            payload = decode_access_token(token)
            if payload and "sub" in payload:
                return f"user_{payload['sub']}"
        except Exception:
            # If token is invalid, fall back to IP
            pass
    
    # Fall back to IP address
    return f"ip_{get_remote_address(request)}"


def get_auth_rate_limit() -> str:
    """Get rate limit string for authentication endpoints"""
    # More restrictive for auth endpoints
    rate_per_minute = max(5, settings.RATE_LIMIT_PER_MINUTE // 12)  # ~5 requests per minute
    return f"{rate_per_minute}/minute"


def get_general_rate_limit() -> str:
    """Get rate limit string for general endpoints"""
    return f"{settings.RATE_LIMIT_PER_MINUTE}/minute"


def get_strict_rate_limit() -> str:
    """Get rate limit string for sensitive operations"""
    # Very restrictive for invitation/password operations
    return "2/minute"


# Rate limit configurations for different endpoint types
RATE_LIMITS = {
    "auth_login": "5/minute",           # Login attempts
    "auth_accept": "3/minute",          # Invitation acceptance  
    "auth_general": "10/minute",        # Other auth operations
    "invitation_create": "10/hour",     # Creating invitations (admin)
    "invitation_get": "30/minute",      # Getting invitation details
    "chat": "20/minute",                # Chat/AI requests (resource intensive)
    "general": f"{settings.RATE_LIMIT_PER_MINUTE}/minute",  # General endpoints
}