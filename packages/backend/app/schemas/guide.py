from pydantic import BaseModel, HttpUrl, Field
from typing import Optional
from datetime import datetime
import uuid


class GuideBase(BaseModel):
    """Base schema for guide data"""
    title: str = Field(..., min_length=1, max_length=255, description="Display title for the guide")
    platform_name: str = Field(..., min_length=1, max_length=255, description="Name of the platform/service")
    where_to_get: Optional[str] = Field(None, description="URL where users can get API keys/credentials")
    guide_link: Optional[str] = Field(None, description="Link to step-by-step guide")
    documentation_link: Optional[str] = Field(None, description="Link to official documentation")
    description: Optional[str] = Field(None, max_length=1000, description="Brief description of the platform")


class GuideCreate(GuideBase):
    """Schema for creating a new guide"""
    pass


class GuideUpdate(BaseModel):
    """Schema for updating an existing guide"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    platform_name: Optional[str] = Field(None, min_length=1, max_length=255)
    where_to_get: Optional[str] = None
    guide_link: Optional[str] = None
    documentation_link: Optional[str] = None
    description: Optional[str] = Field(None, max_length=1000)


class GuideResponse(GuideBase):
    """Schema for guide response"""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GuideListResponse(BaseModel):
    """Schema for paginated guide list response"""
    guides: list[GuideResponse]
    total: int
    page: int = 1
    per_page: int = 50
