"""Chat schemas for requests and responses"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ChatMessage(BaseModel):
    """Schema for chat message requests"""
    message: str = Field(..., min_length=1, max_length=5000, description="Chat message content")
    chatbot_id: str = Field(..., description="ID of the chatbot to send message to")
    conversation_id: Optional[str] = Field(None, description="ID of the conversation")
    user_id: Optional[str] = Field(None, description="ID of the user sending the message")


class ChatResponse(BaseModel):
    """Schema for chat message responses"""
    response: str = Field(description="Response from the chatbot")
    timestamp: datetime = Field(description="Timestamp of the response")
    chatbot_id: str = Field(description="ID of the chatbot")
    conversation_id: Optional[str] = Field(None, description="ID of the conversation")
    message_id: Optional[str] = Field(None, description="ID of the message")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    source: Optional[str] = Field(None, description="Source of the response")


class ChatHistoryResponse(BaseModel):
    """Response for chat history"""
    messages: List[Dict[str, Any]] = Field(description="List of chat messages")
    total: int = Field(description="Total number of messages")
    chatbot_id: str = Field(description="ID of the chatbot")
    conversation_id: Optional[str] = Field(default=None, description="ID of the conversation")


class ConversationListResponse(BaseModel):
    """Response for conversation list"""
    conversations: List[Dict[str, Any]] = Field(description="List of conversations")
    total: int = Field(description="Total number of conversations")
    chatbot_id: str = Field(description="ID of the chatbot")


class ChatTestResponse(BaseModel):
    """Response for chat test endpoint"""
    status: str = Field(description="Service status")
    message: str = Field(description="Service message")
    timestamp: str = Field(description="Timestamp of the response")