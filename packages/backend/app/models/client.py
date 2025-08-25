"""Client model"""

from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class Client(Base, TimestampMixin):
    """Client model for multi-tenant organization"""
    
    __tablename__ = "clients"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Encrypted n8n API key
    n8n_api_key_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    n8n_api_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Admin who created this client
    created_by_admin_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Relationships
    user = relationship("User", back_populates="client", foreign_keys="User.client_id")
    created_by_admin = relationship("User", foreign_keys=[created_by_admin_id])
    
    def __repr__(self) -> str:
        return f"<Client(id={self.id}, name='{self.name}')>"