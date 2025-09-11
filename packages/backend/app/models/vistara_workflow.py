"""Vistara workflow model for curated workflow display"""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, Boolean, DateTime, Text, Float, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from .base import Base, TimestampMixin


class WorkflowCategory(enum.Enum):
    """Workflow category enumeration"""
    AUTOMATION = "Automation"
    INTEGRATION = "Integration"
    ANALYTICS = "Analytics"
    COMMUNICATION = "Communication"
    CUSTOM = "Custom"


class VistaraWorkflow(Base, TimestampMixin):
    """Vistara workflow model for storing curated workflow data"""
    
    __tablename__ = "vistara_workflows"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4()), 
        index=True
    )
    
    # Reference to original workflow (optional - for linking to live data)
    original_workflow_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("workflows.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Client association (for access control)
    client_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Workflow display information
    workflow_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("vistara_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # User-editable content
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    documentation_link: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Metrics data (can be manually entered or synced from original workflow)
    total_executions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    successful_executions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_executions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    # Time metrics
    avg_execution_time_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    manual_time_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)  # Estimated manual time
    time_saved_per_execution_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    total_time_saved_hours: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    # Baseline tracking for incremental sync - stores the original n8n values when manual changes were made
    baseline_total_executions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    baseline_successful_executions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    baseline_failed_executions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    baseline_avg_execution_time_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Manual adjustments - what the user added/changed on top of the original values
    manual_total_executions_adjustment: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    manual_successful_executions_adjustment: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    manual_failed_executions_adjustment: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_execution: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Display order (for custom sorting)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Metadata
    created_by: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Relationships
    client = relationship("Client")
    original_workflow = relationship("Workflow")
    created_by_user = relationship("User")
    category_ref = relationship("VistaraCategory", back_populates="workflows")
    
    def __repr__(self) -> str:
        category_name = self.category_ref.name if self.category_ref else "Uncategorized"
        return f"<VistaraWorkflow(id={self.id}, name='{self.workflow_name}', category='{category_name}')>"
    
    @property
    def execution_time_seconds(self) -> float:
        """Get execution time in seconds"""
        return self.avg_execution_time_ms / 1000.0
    
    @property
    def manual_time_hours(self) -> float:
        """Get manual time in hours"""
        return self.manual_time_minutes / 60.0
    
    @property
    def time_saved_per_execution_hours(self) -> float:
        """Get time saved per execution in hours"""
        return self.time_saved_per_execution_minutes / 60.0
    
    async def update_metrics_from_original(self, db_session):
        """Update metrics from the original workflow if linked"""
        if not self.original_workflow_id:
            return False
        
        from sqlalchemy import select, func, and_, text
        from .workflow_execution import WorkflowExecution, ExecutionStatus
        
        try:
            # Use simple separate queries for maximum compatibility
            base_filter = and_(
                WorkflowExecution.workflow_id == self.original_workflow_id,
                WorkflowExecution.is_production == True
            )
            
            # Get total count
            total_query = select(func.count(WorkflowExecution.id)).where(base_filter)
            total_result = await db_session.execute(total_query)
            total_executions = total_result.scalar() or 0
            
            # Get successful count
            success_query = select(func.count(WorkflowExecution.id)).where(
                and_(base_filter, WorkflowExecution.status == ExecutionStatus.SUCCESS)
            )
            success_result = await db_session.execute(success_query)
            successful_executions = success_result.scalar() or 0
            
            # Get failed count
            error_query = select(func.count(WorkflowExecution.id)).where(
                and_(base_filter, WorkflowExecution.status == ExecutionStatus.ERROR)
            )
            error_result = await db_session.execute(error_query)
            failed_executions = error_result.scalar() or 0
            
            # Get timing metrics
            timing_query = select(
                func.avg(WorkflowExecution.execution_time_ms).label('avg_execution_time_ms'),
                func.max(WorkflowExecution.started_at).label('last_execution')
            ).where(base_filter)
            
            timing_result = await db_session.execute(timing_query)
            timing_metrics = timing_result.first()
            
            # Get current n8n values
            current_n8n_total = int(total_executions)
            current_n8n_successful = int(successful_executions)
            current_n8n_failed = int(failed_executions)
            current_n8n_avg_time = int(timing_metrics.avg_execution_time_ms or 0) if timing_metrics else 0
            
            # Update execution stats with incremental logic:
            # Final value = Current n8n value + Manual adjustment
            self.total_executions = current_n8n_total + self.manual_total_executions_adjustment
            self.successful_executions = current_n8n_successful + self.manual_successful_executions_adjustment
            self.failed_executions = current_n8n_failed + self.manual_failed_executions_adjustment
            
            # Ensure values are not negative
            self.total_executions = max(0, self.total_executions)
            self.successful_executions = max(0, self.successful_executions)
            self.failed_executions = max(0, self.failed_executions)
            
            # Calculate success rate based on final values
            if self.total_executions > 0:
                self.success_rate = round((self.successful_executions / self.total_executions) * 100, 2)
            else:
                self.success_rate = 0.0
            
            # Update execution time and last execution (always use current n8n values)
            self.avg_execution_time_ms = current_n8n_avg_time
            if timing_metrics:
                self.last_execution = timing_metrics.last_execution
            else:
                self.last_execution = None
            
            # Auto-calculate time saved metrics based on current values
            # Calculate time saved per execution: manual_time_minutes - (avg_execution_time_ms / 60000)
            execution_time_minutes = self.avg_execution_time_ms / 60000
            time_saved_per_run = max(0, self.manual_time_minutes - execution_time_minutes)
            self.time_saved_per_execution_minutes = int(round(time_saved_per_run))
            
            # Calculate total time saved based on successful executions (including manual adjustments)
            if self.successful_executions > 0:
                time_saved_minutes = self.successful_executions * self.time_saved_per_execution_minutes
                self.total_time_saved_hours = round(time_saved_minutes / 60.0, 2)
            else:
                self.total_time_saved_hours = 0.0
            
            # Update baselines to current n8n values for future calculations
            self.baseline_total_executions = current_n8n_total
            self.baseline_successful_executions = current_n8n_successful
            self.baseline_failed_executions = current_n8n_failed
            self.baseline_avg_execution_time_ms = current_n8n_avg_time
            
            return True
            
        except Exception as e:
            # Log the error but don't raise it to avoid breaking the sync process
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to sync metrics for Vistara workflow {self.id}: {e}")
            return False
