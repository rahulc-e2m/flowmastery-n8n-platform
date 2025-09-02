"""Metrics aggregation models for persistent storage"""

import uuid
from datetime import datetime, date, timezone
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, Boolean, DateTime, Date, Float, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from .base import Base, TimestampMixin


class AggregationPeriod(enum.Enum):
    """Aggregation period enumeration"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class MetricsAggregation(Base, TimestampMixin):
    """Metrics aggregation model for storing computed metrics by period"""
    
    __tablename__ = "metrics_aggregations"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # Client association
    client_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Workflow association (optional - can be null for client-wide metrics)
    workflow_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Aggregation details
    period_type: Mapped[AggregationPeriod] = mapped_column(
        Enum(AggregationPeriod),
        nullable=False,
        index=True
    )
    
    period_start: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Execution metrics
    total_executions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    successful_executions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_executions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    canceled_executions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Performance metrics
    success_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    avg_execution_time_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    min_execution_time_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_execution_time_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Data volume metrics
    total_data_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    avg_data_size_bytes: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Workflow metrics (for client-wide aggregations)
    total_workflows: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    active_workflows: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Error analysis
    most_common_error: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Additional computed metrics
    time_saved_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Estimated time saved through automation
    productivity_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Custom productivity metric
    
    # Computation timestamp
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    client = relationship("Client")
    workflow = relationship("Workflow", foreign_keys=[workflow_id])
    
    def __repr__(self) -> str:
        return f"<MetricsAggregation(id={self.id}, client_id={self.client_id}, period={self.period_type.value}, start={self.period_start})>"
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate as percentage"""
        if self.total_executions > 0:
            return (self.failed_executions / self.total_executions) * 100.0
        return 0.0
    
    @property
    def completion_rate(self) -> float:
        """Calculate completion rate (successful + failed / total)"""
        if self.total_executions > 0:
            completed = self.successful_executions + self.failed_executions
            return (completed / self.total_executions) * 100.0
        return 0.0


class WorkflowTrendMetrics(Base, TimestampMixin):
    """Workflow trend metrics for tracking performance changes over time"""
    
    __tablename__ = "workflow_trend_metrics"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # Workflow association
    workflow_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Client association
    client_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Trend period
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    
    # Daily metrics
    executions_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Performance metrics
    avg_duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Trend indicators
    success_rate_trend: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Compared to previous period
    performance_trend: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Execution time trend
    
    # Relationships
    workflow = relationship("Workflow")
    client = relationship("Client")
    
    def __repr__(self) -> str:
        return f"<WorkflowTrendMetrics(id={self.id}, workflow_id={self.workflow_id}, date={self.date})>"