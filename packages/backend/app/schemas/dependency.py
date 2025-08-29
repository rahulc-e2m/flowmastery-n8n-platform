from pydantic import BaseModel, HttpUrl, Field
from typing import Optional
from datetime import datetime
import uuid


class DependencyBase(BaseModel):
    """Base schema for dependency data"""
    platform_name: str = Field(..., min_length=1, max_length=255, description="Name of the platform/service")
    where_to_get: Optional[str] = Field(None, description="URL where users can get API keys/credentials")
    guide_link: Optional[str] = Field(None, description="Link to step-by-step guide")
    documentation_link: Optional[str] = Field(None, description="Link to official documentation")
    description: Optional[str] = Field(None, max_length=1000, description="Brief description of the platform")


class DependencyCreate(DependencyBase):
    """Schema for creating a new dependency"""
    pass


class DependencyUpdate(BaseModel):
    """Schema for updating an existing dependency"""
    platform_name: Optional[str] = Field(None, min_length=1, max_length=255)
    where_to_get: Optional[str] = None
    guide_link: Optional[str] = None
    documentation_link: Optional[str] = None
    description: Optional[str] = Field(None, max_length=1000)


class DependencyResponse(DependencyBase):
    """Schema for dependency response"""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DependencyListResponse(BaseModel):
    """Schema for paginated dependency list response"""
    dependencies: list[DependencyResponse]
    total: int
    page: int = 1
    per_page: int = 50