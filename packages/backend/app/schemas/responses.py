"""Resource-specific standardized response models"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.schemas.api_standard import (
    StandardResponse,
    ResourceCreatedResponse,
    ResourceUpdatedResponse,
    ResourceDeletedResponse,
    ListResponse,
    PaginatedResponse
)
from app.schemas.client import ClientResponse
from app.schemas.chatbot import ChatbotResponse
from app.schemas.cache import CacheClearResponse, CacheStatsResponse
from app.schemas.config import ConfigStatusResponse


# Client-specific responses
class ClientCreatedResponse(ResourceCreatedResponse[ClientResponse]):
    """Response for client creation"""
    message: str = "Client created successfully"
    location: Optional[str] = Field(None, description="Location of the created client")


class ClientUpdatedResponse(ResourceUpdatedResponse[ClientResponse]):
    """Response for client updates"""
    message: str = "Client updated successfully"


class ClientDeletedResponse(ResourceDeletedResponse):
    """Response for client deletion"""
    message: str = "Client deleted successfully"


class ClientListResponse(ListResponse[ClientResponse]):
    """Response for client list operations"""
    message: str = "Clients retrieved successfully"


# Chatbot-specific responses
class ChatbotCreatedResponse(ResourceCreatedResponse[ChatbotResponse]):
    """Response for chatbot creation"""
    message: str = "Chatbot created successfully"


class ChatbotUpdatedResponse(ResourceUpdatedResponse[ChatbotResponse]):
    """Response for chatbot updates"""
    message: str = "Chatbot updated successfully"


class ChatbotDeletedResponse(ResourceDeletedResponse):
    """Response for chatbot deletion"""
    message: str = "Chatbot deleted successfully"


class ChatbotListResponse(ListResponse[ChatbotResponse]):
    """Response for chatbot list operations"""
    message: str = "Chatbots retrieved successfully"


# Workflow-specific responses
class WorkflowResponse(BaseModel):
    """Standard workflow response model"""
    id: str
    name: str
    active: bool
    client_id: str
    client_name: Optional[str] = None
    time_saved_per_execution_minutes: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class WorkflowUpdatedResponse(ResourceUpdatedResponse[WorkflowResponse]):
    """Response for workflow updates"""
    message: str = "Workflow updated successfully"


class WorkflowListResponse(ListResponse[WorkflowResponse]):
    """Response for workflow list operations"""
    message: str = "Workflows retrieved successfully"


# Cache-specific responses
class CacheClearSuccessResponse(StandardResponse[CacheClearResponse]):
    """Response for cache clear operations"""
    message: str = "Cache cleared successfully"


class CacheStatsSuccessResponse(StandardResponse[CacheStatsResponse]):
    """Response for cache stats operations"""
    message: str = "Cache statistics retrieved successfully"


# Configuration-specific responses
class ConfigStatusSuccessResponse(StandardResponse[ConfigStatusResponse]):
    """Response for configuration status"""
    message: str = "Configuration status retrieved successfully"


# Health check responses
class HealthResponse(BaseModel):
    """Health check response data"""
    status: str = Field(description="Service health status")
    version: str = Field(description="Application version")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    uptime: Optional[str] = Field(None, description="Service uptime")
    environment: Optional[str] = Field(None, description="Environment name")


class HealthCheckSuccessResponse(StandardResponse[HealthResponse]):
    """Response for health check operations"""
    message: str = "Health check completed successfully"


class DetailedHealthResponse(HealthResponse):
    """Detailed health check response data"""
    services: Dict[str, Any] = Field(default_factory=dict, description="Service status details")
    database: Dict[str, Any] = Field(default_factory=dict, description="Database status")
    cache: Dict[str, Any] = Field(default_factory=dict, description="Cache status")
    external_apis: Dict[str, Any] = Field(default_factory=dict, description="External API status")


class DetailedHealthCheckSuccessResponse(StandardResponse[DetailedHealthResponse]):
    """Response for detailed health check operations"""
    message: str = "Detailed health check completed successfully"


# Authentication responses
class LoginResponse(BaseModel):
    """Login response data"""
    access_token: str = Field(description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(description="Token expiration time in seconds")
    user_id: str = Field(description="User ID")
    role: str = Field(description="User role")
    client_id: Optional[str] = Field(None, description="Client ID for client users")


class LoginSuccessResponse(StandardResponse[LoginResponse]):
    """Response for successful login"""
    message: str = "Login successful"


class LogoutResponse(BaseModel):
    """Logout response data"""
    message: str = "Logout successful"


class LogoutSuccessResponse(StandardResponse[LogoutResponse]):
    """Response for successful logout"""
    message: str = "Logout completed successfully"


# Metrics responses
class MetricsResponse(BaseModel):
    """Metrics response data"""
    total_workflows: int = Field(description="Total number of workflows")
    active_workflows: int = Field(description="Number of active workflows")
    total_executions: int = Field(description="Total number of executions")
    successful_executions: int = Field(description="Number of successful executions")
    failed_executions: int = Field(description="Number of failed executions")
    total_time_saved_minutes: float = Field(description="Total time saved in minutes")
    period_start: datetime = Field(description="Metrics period start")
    period_end: datetime = Field(description="Metrics period end")


class MetricsSuccessResponse(StandardResponse[MetricsResponse]):
    """Response for metrics operations"""
    message: str = "Metrics retrieved successfully"


# Task responses
class TaskResponse(BaseModel):
    """Task response data"""
    task_id: str = Field(description="Task ID")
    status: str = Field(description="Task status")
    result: Optional[Any] = Field(None, description="Task result")
    error: Optional[str] = Field(None, description="Task error message")
    created_at: datetime = Field(description="Task creation time")
    completed_at: Optional[datetime] = Field(None, description="Task completion time")


class TaskSuccessResponse(StandardResponse[TaskResponse]):
    """Response for task operations"""
    message: str = "Task retrieved successfully"


class TaskListResponse(ListResponse[TaskResponse]):
    """Response for task list operations"""
    message: str = "Tasks retrieved successfully"


# Chat responses
class ChatMessageResponse(BaseModel):
    """Chat message response data"""
    message_id: str = Field(description="Message ID")
    content: str = Field(description="Message content")
    sender: str = Field(description="Message sender")
    timestamp: datetime = Field(description="Message timestamp")
    chatbot_id: str = Field(description="Chatbot ID")
    conversation_id: str = Field(description="Conversation ID")


class ChatMessageSuccessResponse(StandardResponse[ChatMessageResponse]):
    """Response for chat message operations"""
    message: str = "Chat message processed successfully"


class ChatHistoryResponse(BaseModel):
    """Chat history response data"""
    messages: List[ChatMessageResponse] = Field(description="Chat messages")
    total: int = Field(description="Total number of messages")
    chatbot_id: str = Field(description="Chatbot ID")
    conversation_id: str = Field(description="Conversation ID")


class ChatHistorySuccessResponse(StandardResponse[ChatHistoryResponse]):
    """Response for chat history operations"""
    message: str = "Chat history retrieved successfully"