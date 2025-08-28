"""Workflow model for persistent storage"""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, Boolean, DateTime, Text, JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class Workflow(Base, TimestampMixin):
    """Workflow model for storing n8n workflow data"""
    
    __tablename__ = "workflows"
    __table_args__ = (
        UniqueConstraint('client_id', 'n8n_workflow_id', name='uq_workflows_client_n8n_id'),
    )
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # n8n workflow identifier (unique per client)
    n8n_workflow_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Client association
    client_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Workflow details
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Workflow metadata
    tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string of tags
    nodes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Number of nodes
    connections: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Number of connections
    
    # Timestamps from n8n
    n8n_created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    n8n_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Additional workflow settings
    settings: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string of settings
    
    # Estimated minutes saved per successful execution (editable)
    time_saved_per_execution_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    
    # Last sync information
    last_synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        default=datetime.utcnow
    )
    
    # Relationships
    client = relationship("Client", back_populates="workflows")
    executions = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Workflow(id={self.id}, name='{self.name}', client_id={self.client_id})>"