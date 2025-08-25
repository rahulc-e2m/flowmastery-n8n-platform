"""User model"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """User model for authentication and authorization"""
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # 'admin' or 'client'
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # For client users - link to their client record
    client_id: Mapped[Optional[int]] = mapped_column(
        Integer, 
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=True
    )
    
    # Who created this user (for audit trail)
    created_by_admin_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Last login tracking
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    client = relationship("Client", back_populates="user", foreign_keys=[client_id])
    created_by_admin = relationship("User", remote_side=[id])
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"