"""Client schemas"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ClientBase(BaseModel):
    """Base client schema"""
    name: str = Field(..., min_length=1, max_length=255)


class ClientCreate(ClientBase):
    """Schema for creating a client"""
    pass


class ClientUpdate(BaseModel):
    """Schema for updating a client"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    n8n_api_url: Optional[str] = Field(None, max_length=500)


class ClientResponse(ClientBase):
    """Schema for client response"""
    id: str
    n8n_api_url: Optional[str] = None
    has_n8n_api_key: bool = False  # Don't expose the actual key
    created_at: datetime
    
    model_config = {"from_attributes": True}


class ClientN8nConfig(BaseModel):
    """Schema for configuring client's n8n API"""
    n8n_api_url: str = Field(..., max_length=500)
    n8n_api_key: str = Field(..., min_length=1)


class N8nConnectionTestResponse(BaseModel):
    """Schema for n8n connection test response"""
    status: str  # success, warning, error
    connection_healthy: bool
    api_accessible: bool
    message: str
    instance_info: Dict[str, Any] = {}


class ClientSyncResponse(BaseModel):
    """Schema for client sync response"""
    message: str
    client_id: str
    client_name: str
    immediate_sync_triggered: bool
    note: str