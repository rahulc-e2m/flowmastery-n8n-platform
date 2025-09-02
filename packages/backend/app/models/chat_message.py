"""Chat message model for storing conversation history"""

import uuid
from sqlalchemy import String, Text, DateTime, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin
from datetime import datetime
from typing import Optional


class ChatMessage(Base, TimestampMixin):
    """Chat message model for storing conversation history"""
    
    __tablename__ = "chat_messages"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    chatbot_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("chatbots.id"), nullable=False)
    conversation_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    user_message: Mapped[str] = mapped_column(Text, nullable=False)
    bot_response: Mapped[str] = mapped_column(Text, nullable=False)
    processing_time: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)  # webhook, ai, fallback, etc.
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    chatbot = relationship("Chatbot", back_populates="messages")