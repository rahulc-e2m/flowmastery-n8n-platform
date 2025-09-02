"""Chat-related schemas"""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ChatMessage(BaseModel):
    """Chat message request"""
    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    chatbot_id: str = Field(..., description="Chatbot identifier")
    conversation_id: Optional[str] = Field(None, description="Conversation identifier")


class ChatResponse(BaseModel):
    """Chat response"""
    response: str = Field(..., description="Bot response")
    message_id: str = Field(..., description="Unique message identifier")
    timestamp: str = Field(..., description="Response timestamp")
    processing_time: float = Field(..., description="Processing time in seconds")
    source: str = Field(..., description="Response source (ai, n8n, fallback)")
    conversation_id: Optional[str] = Field(None, description="Conversation identifier")


class ChatHistory(BaseModel):
    """Chat history entry"""
    message_id: str
    user_message: str
    bot_response: str
    timestamp: datetime
    processing_time: float
    source: str