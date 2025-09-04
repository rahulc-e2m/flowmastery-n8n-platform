"""FastAPI dependencies for authentication and authorization"""

from typing import Optional, List
from fastapi import Depends, HTTPException, status, Request

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.client import Client
from app.core.auth import verify_token
from app.core.user_roles import UserRole, RolePermissions




def get_current_user(
    required_roles: Optional[List[UserRole]] = None,
    allow_inactive: bool = False
):
    """
    Dependency factory for getting current authenticated user with role-based access control.
    
    Args:
        required_roles: List of roles that are allowed to access the endpoint
        allow_inactive: Whether to allow inactive users (default: False)
    
    Returns:
        Dependency function that returns the current user
    """
    async def _get_current_user(
        request: Request,
        db: AsyncSession = Depends(get_db)
    ) -> User:
        """Get the current authenticated user from httpOnly cookie"""
        token = request.cookies.get("access_token")
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No access token found in cookies",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        payload = verify_token(token)
        
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        
        # User ID is now a UUID string, no conversion needed
        user_id = user_id_str
        
        # Get user from database
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if not allow_inactive and not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user"
            )
        
        # Check role permissions if required_roles is specified
        if required_roles:
            try:
                user_role = UserRole(user.role)
                if user_role not in required_roles:
                    role_names = [role.value for role in required_roles]
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Access denied. Required roles: {', '.join(role_names)}"
                    )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Invalid user role: {user.role}"
                )
        
        return user
    
    return _get_current_user


# Convenience functions for backward compatibility and common use cases
async def get_current_admin_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get the current user and ensure they are an admin"""
    return await get_current_user(required_roles=[UserRole.ADMIN])(request, db)


async def get_current_client_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get the current user and ensure they are a client"""
    return await get_current_user(required_roles=[UserRole.CLIENT])(request, db)


async def get_client_for_user(
    current_user: User = Depends(get_current_user(required_roles=[UserRole.CLIENT])),
    db: AsyncSession = Depends(get_db)
) -> Client:
    """Get the client associated with the current user"""
    if not current_user.client_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No client associated with user"
        )
    
    result = await db.execute(select(Client).where(Client.id == current_user.client_id))
    client = result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    return client


def verify_client_access(client_id: str):
    """Dependency factory to verify client access"""
    async def _verify_client_access(
        current_user: User = Depends(get_current_user(required_roles=[UserRole.ADMIN, UserRole.CLIENT])),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        # Admins can access any client
        if RolePermissions.is_admin(current_user.role):
            return current_user
        
        # Clients can only access their own data
        if RolePermissions.is_client(current_user.role):
            if current_user.client_id != client_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this client's data"
                )
            return current_user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid role"
        )
    
    return _verify_client_access





# Additional convenience functions for common role combinations
def get_any_authenticated_user():
    """Get any authenticated user regardless of role"""
    return get_current_user()


def get_admin_or_client_user():
    """Get user that is either admin or client"""
    return get_current_user(required_roles=[UserRole.ADMIN, UserRole.CLIENT])


async def get_optional_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Get the current authenticated user from httpOnly cookie, return None if not authenticated"""
    token = request.cookies.get("access_token")
    
    if not token:
        return None
    
    try:
        payload = verify_token(token)
        
        user_id_str = payload.get("sub")
        if user_id_str is None:
            return None
        
        # Get user from database
        result = await db.execute(select(User).where(User.id == user_id_str))
        user = result.scalar_one_or_none()
        
        if user is None or not user.is_active:
            return None
        
        return user
    except Exception:
        return None