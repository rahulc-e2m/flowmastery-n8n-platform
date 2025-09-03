"""Cache management response schemas"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class CacheClearResponse(BaseModel):
    """Response for cache clearing operations"""
    message: str = Field(description="Description of the operation performed")
    keys_cleared: int = Field(description="Number of cache keys cleared")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CacheStatsResponse(BaseModel):
    """Response for cache statistics"""
    cached_workflows: int = Field(description="Number of cached workflows")
    cached_executions: int = Field(description="Number of cached executions")
    cached_metrics: int = Field(description="Number of cached metrics")
    total_cached_items: int = Field(description="Total number of cached items")
    error: Optional[str] = Field(default=None, description="Error message if operation failed")


class ClientCacheClearResponse(BaseModel):
    """Response for client-specific cache clearing"""
    message: str = Field(description="Description of the operation performed")
    client_id: str = Field(description="ID of the client whose cache was cleared")
    keys_cleared: int = Field(description="Number of cache keys cleared")
    timestamp: datetime = Field(default_factory=datetime.utcnow)