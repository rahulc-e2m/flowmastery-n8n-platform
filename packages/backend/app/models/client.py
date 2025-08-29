"""Client model"""

import uuid
from typing import Optional
from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class Client(Base, TimestampMixin):
    """Client model for multi-tenant organization"""
    
    __tablename__ = "clients"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Encrypted n8n API key
    n8n_api_key_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    n8n_api_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Admin who created this client
    created_by_admin_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Relationships
    user = relationship("User", back_populates="client", foreign_keys="User.client_id")
    created_by_admin = relationship("User", foreign_keys=[created_by_admin_id])
    workflows = relationship("Workflow", back_populates="client", cascade="all, delete-orphan")
    chatbots = relationship("Chatbot", back_populates="client", cascade="all, delete-orphan")
    sync_state = relationship("SyncState", back_populates="client", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Client(id={self.id}, name='{self.name}')>"