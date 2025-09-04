"""User role definitions and utilities"""

from enum import Enum
from typing import List


class UserRole(str, Enum):
    """User role enumeration"""
    ADMIN = "admin"
    CLIENT = "client"
    VIEWER = "viewer"  # Future role for read-only access


class RolePermissions:
    """Role-based permission definitions"""
    
    # Roles that can access admin endpoints
    ADMIN_ROLES: List[UserRole] = [UserRole.ADMIN]
    
    # Roles that can access client-specific data
    CLIENT_ROLES: List[UserRole] = [UserRole.CLIENT, UserRole.VIEWER]
    
    # All valid roles
    ALL_ROLES: List[UserRole] = [UserRole.ADMIN, UserRole.CLIENT, UserRole.VIEWER]
    
    @classmethod
    def is_admin(cls, role: str) -> bool:
        """Check if role has admin permissions"""
        return UserRole(role) in cls.ADMIN_ROLES
    
    @classmethod
    def is_client(cls, role: str) -> bool:
        """Check if role has client permissions"""
        return UserRole(role) in cls.CLIENT_ROLES
    
    @classmethod
    def can_access_client_data(cls, role: str) -> bool:
        """Check if role can access client-specific data"""
        return UserRole(role) in cls.CLIENT_ROLES or UserRole(role) in cls.ADMIN_ROLES