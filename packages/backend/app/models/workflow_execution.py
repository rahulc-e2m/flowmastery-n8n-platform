"""Workflow execution model for persistent storage"""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, Boolean, DateTime, Text, Float, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from .base import Base, TimestampMixin


class ExecutionStatus(enum.Enum):
    """Execution status enumeration"""
    SUCCESS = "success"
    ERROR = "error"
    WAITING = "waiting"
    RUNNING = "running"
    CANCELED = "canceled"
    CRASHED = "crashed"
    NEW = "new"


class ExecutionMode(enum.Enum):
    """Execution mode enumeration"""
    MANUAL = "manual"
    TRIGGER = "trigger"
    RETRY = "retry"
    WEBHOOK = "webhook"
    ERROR_TRIGGER = "error_trigger"


class WorkflowExecution(Base, TimestampMixin):
    """Workflow execution model for storing n8n execution data"""
    
    __tablename__ = "workflow_executions"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # n8n execution identifier
    n8n_execution_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    
    # Workflow association
    workflow_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Client association (for easier querying)
    client_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Execution details
    status: Mapped[ExecutionStatus] = mapped_column(
        Enum(ExecutionStatus),
        nullable=False,
        index=True
    )
    
    mode: Mapped[Optional[ExecutionMode]] = mapped_column(
        Enum(ExecutionMode),
        nullable=True
    )
    
    # Timing information
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    stopped_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Performance metrics
    execution_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Duration in milliseconds
    
    # Production flag (to filter out test/dev runs)
    is_production: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    
    # Error information
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Additional execution data
    data_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Size of execution data
    node_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Number of nodes executed
    
    # Retry information
    retry_of: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Original execution ID if this is a retry
    retry_count: Mapped[Optional[int]] = mapped_column(Integer, default=0, nullable=True)
    
    # Last sync information
    last_synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        default=datetime.utcnow
    )
    
    # Relationships
    workflow = relationship("Workflow", back_populates="executions")
    client = relationship("Client")
    
    def __repr__(self) -> str:
        return f"<WorkflowExecution(id={self.id}, status={self.status.value}, workflow_id={self.workflow_id})>"
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate execution duration in seconds"""
        if self.started_at and self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        elif self.execution_time_ms:
            return self.execution_time_ms / 1000.0
        return None
    
    @property
    def is_successful(self) -> bool:
        """Check if execution was successful"""
        return self.status == ExecutionStatus.SUCCESS
    
    @property
    def is_failed(self) -> bool:
        """Check if execution failed"""
        return self.status in [ExecutionStatus.ERROR, ExecutionStatus.CRASHED]