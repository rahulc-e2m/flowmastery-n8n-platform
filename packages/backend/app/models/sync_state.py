"""Sync state model for tracking synchronization history"""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, DateTime, Text, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class SyncState(Base, TimestampMixin):
    """Model to track sync state for each client"""
    
    __tablename__ = "sync_states"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # Client association
    client_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One sync state per client
        index=True
    )
    
    # Last successful sync timestamps
    last_workflow_sync: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    
    last_execution_sync: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    
    # Track the last execution ID we've seen (for incremental sync)
    last_execution_id: Mapped[Optional[str]] = mapped_column(
        String(255), 
        nullable=True
    )
    
    # Track the oldest execution date we've fetched
    oldest_execution_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    
    # Track the most recent execution date we've fetched
    newest_execution_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    
    # Pagination cursor for next sync
    sync_cursor: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True
    )
    
    # Track last aggregation computation dates
    last_daily_aggregation: Mapped[Optional[Date]] = mapped_column(
        Date, 
        nullable=True
    )
    
    last_weekly_aggregation: Mapped[Optional[Date]] = mapped_column(
        Date, 
        nullable=True
    )
    
    last_monthly_aggregation: Mapped[Optional[Date]] = mapped_column(
        Date, 
        nullable=True
    )
    
    # Track sync statistics
    total_workflows_synced: Mapped[int] = mapped_column(
        Integer, 
        default=0, 
        nullable=False
    )
    
    total_executions_synced: Mapped[int] = mapped_column(
        Integer, 
        default=0, 
        nullable=False
    )
    
    # Track any sync errors
    last_error: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True
    )
    
    last_error_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    
    # Relationships
    client = relationship("Client", back_populates="sync_state")
    
    def __repr__(self) -> str:
        return f"<SyncState(id={self.id}, client_id={self.client_id}, last_execution_sync={self.last_execution_sync})>"
    
    def update_execution_sync(
        self, 
        execution_count: int,
        newest_date: Optional[datetime] = None,
        oldest_date: Optional[datetime] = None,
        last_id: Optional[str] = None
    ):
        """Update execution sync state"""
        self.last_execution_sync = datetime.utcnow()
        self.total_executions_synced += execution_count
        
        if newest_date and (not self.newest_execution_date or newest_date > self.newest_execution_date):
            self.newest_execution_date = newest_date
            
        if oldest_date and (not self.oldest_execution_date or oldest_date < self.oldest_execution_date):
            self.oldest_execution_date = oldest_date
            
        if last_id:
            self.last_execution_id = last_id
    
    def update_workflow_sync(self, workflow_count: int):
        """Update workflow sync state"""
        self.last_workflow_sync = datetime.utcnow()
        self.total_workflows_synced = workflow_count
    
    def record_error(self, error_message: str):
        """Record sync error"""
        self.last_error = error_message[:1000]  # Truncate long errors
        self.last_error_at = datetime.utcnow()
