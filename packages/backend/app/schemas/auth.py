"""Authentication schemas"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    role: str
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if v not in ['admin', 'client']:
            raise ValueError('Role must be either admin or client')
        return v


class UserCreate(UserBase):
    """Schema for creating a user"""
    password: str = Field(..., min_length=8)


class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    is_active: bool
    client_id: Optional[int] = None
    created_at: datetime
    last_login: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class InvitationCreate(BaseModel):
    """Schema for creating an invitation"""
    email: EmailStr
    role: str
    client_id: Optional[int] = None
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if v not in ['admin', 'client']:
            raise ValueError('Role must be either admin or client')
        return v


class InvitationResponse(BaseModel):
    """Schema for invitation response"""
    id: int
    email: EmailStr
    role: str
    status: str
    expiry_date: datetime
    client_id: Optional[int] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}


class InvitationAccept(BaseModel):
    """Schema for accepting an invitation"""
    token: str
    password: str = Field(..., min_length=8)


class PasswordChange(BaseModel):
    """Schema for changing password"""
    current_password: str
    new_password: str = Field(..., min_length=8)