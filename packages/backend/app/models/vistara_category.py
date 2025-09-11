"""Vistara category model for dynamic category management"""

import uuid
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class VistaraCategory(Base, TimestampMixin):
    """Vistara category model for storing workflow categories"""
    
    __tablename__ = "vistara_categories"
    __table_args__ = (
        UniqueConstraint('name', name='uq_vistara_categories_global_name'),
    )
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4()), 
        index=True
    )
    
    # Client association (optional for global Vistara categories)
    client_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Category details
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Visual styling
    color: Mapped[str] = mapped_column(String(7), nullable=False, default="#6B46C1")  # Hex color code
    icon_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Icon identifier
    
    # Status and ordering
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # System/default flag (prevents deletion of system categories)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Metadata
    created_by: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Relationships
    client = relationship("Client")
    created_by_user = relationship("User")
    workflows = relationship("VistaraWorkflow", back_populates="category_ref")
    
    def __repr__(self) -> str:
        return f"<VistaraCategory(id={self.id}, name='{self.name}', client_id={self.client_id})>"
    
    @property
    def workflow_count(self) -> int:
        """Count of workflows using this category"""
        return len(self.workflows) if self.workflows else 0
    
    def can_delete(self) -> bool:
        """Check if category can be deleted (not system and no workflows)"""
        return not self.is_system and self.workflow_count == 0
