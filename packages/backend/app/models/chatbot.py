"""Chatbot model"""

import uuid
from typing import Optional
from sqlalchemy import String, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class Chatbot(Base, TimestampMixin):
    """Chatbot model for managing AI chatbot instances"""
    
    __tablename__ = "chatbots"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    webhook_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Client relationship
    client_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # User who created this chatbot
    created_by_user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Relationships
    client = relationship("Client", back_populates="chatbots")
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    messages = relationship("ChatMessage", back_populates="chatbot")
    
    def __repr__(self) -> str:
        return f"<Chatbot(id={self.id}, name='{self.name}', client_id='{self.client_id}')>"