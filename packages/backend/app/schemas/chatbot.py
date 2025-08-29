"""Chatbot schemas"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


class ChatbotBase(BaseModel):
    """Base chatbot schema"""
    name: str = Field(..., min_length=1, max_length=255, description="Chatbot name")
    description: Optional[str] = Field(None, max_length=1000, description="Chatbot description")
    webhook_url: str = Field(..., min_length=1, max_length=1000, description="Webhook URL for the chatbot")
    is_active: bool = Field(True, description="Whether the chatbot is active")


class ChatbotCreate(ChatbotBase):
    """Schema for creating a chatbot"""
    client_id: str = Field(..., description="Client ID that owns this chatbot")


class ChatbotUpdate(BaseModel):
    """Schema for updating a chatbot"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Chatbot name")
    description: Optional[str] = Field(None, max_length=1000, description="Chatbot description")
    webhook_url: Optional[str] = Field(None, min_length=1, max_length=1000, description="Webhook URL for the chatbot")
    is_active: Optional[bool] = Field(None, description="Whether the chatbot is active")
    client_id: Optional[str] = Field(None, description="Client ID that owns this chatbot")


class ChatbotResponse(ChatbotBase):
    """Schema for chatbot response"""
    id: str
    client_id: str
    client_name: str
    created_by_user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatbotListResponse(BaseModel):
    """Schema for chatbot list response"""
    chatbots: list[ChatbotResponse]
    total: int


class ChatMessage(BaseModel):
    """Schema for chat messages"""
    message: str = Field(..., min_length=1, max_length=5000, description="Chat message content")
    timestamp: Optional[datetime] = Field(None, description="Message timestamp")


class ChatResponse(BaseModel):
    """Schema for chat response"""
    response: str
    timestamp: datetime
    chatbot_id: str