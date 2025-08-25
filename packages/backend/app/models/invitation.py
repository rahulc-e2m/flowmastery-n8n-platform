"""Invitation model"""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class Invitation(Base, TimestampMixin):
    """Invitation model for user registration"""
    
    __tablename__ = "invitations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # 'admin' or 'client'
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)  # 'pending', 'accepted', 'expired'
    
    # Expiry date (default 7 days from creation)
    expiry_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.utcnow() + timedelta(days=7),
        nullable=False
    )
    
    # Admin who sent the invitation
    invited_by_admin_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # For client invitations - which client they'll be associated with
    client_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=True
    )
    
    # When accepted, link to the created user
    accepted_user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # When the invitation was accepted
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    invited_by_admin = relationship("User", foreign_keys=[invited_by_admin_id])
    client = relationship("Client", foreign_keys=[client_id])
    accepted_user = relationship("User", foreign_keys=[accepted_user_id])
    
    @property
    def is_expired(self) -> bool:
        """Check if invitation is expired"""
        return datetime.utcnow() > self.expiry_date
    
    def __repr__(self) -> str:
        return f"<Invitation(id={self.id}, email='{self.email}', role='{self.role}', status='{self.status}')>"