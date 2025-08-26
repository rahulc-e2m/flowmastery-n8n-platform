"""Metrics schemas"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class WorkflowMetrics(BaseModel):
    """Schema for individual workflow metrics"""
    workflow_id: str
    workflow_name: str
    total_executions: int
    successful_executions: int
    failed_executions: int
    success_rate: float
    avg_execution_time: Optional[float] = None
    last_execution: Optional[datetime] = None
    status: str  # 'active', 'inactive', 'error'


class ClientMetrics(BaseModel):
    """Schema for client-level aggregated metrics"""
    client_id: int
    client_name: str
    total_workflows: int
    active_workflows: int
    total_executions: int
    successful_executions: int
    failed_executions: int
    success_rate: float
    avg_execution_time: Optional[float] = None
    last_activity: Optional[datetime] = None
    last_updated: Optional[datetime] = None  # When metrics were last computed


class ClientWorkflowMetrics(BaseModel):
    """Schema for client's workflow-level metrics"""
    client_id: int
    client_name: str
    workflows: List[WorkflowMetrics]
    summary: ClientMetrics


class AdminMetricsResponse(BaseModel):
    """Schema for admin metrics response (all clients)"""
    clients: List[ClientMetrics]
    total_clients: int
    total_workflows: int
    total_executions: int
    overall_success_rate: float
    last_updated: Optional[datetime] = None  # When admin metrics were last computed


class MetricsError(BaseModel):
    """Schema for metrics error response"""
    error: str
    client_id: int
    client_name: str
    details: Optional[str] = None


class MetricsTrend(BaseModel):
    """Schema for metrics trend indicators"""
    execution_trend: float  # Percentage change in executions
    success_rate_trend: float  # Change in success rate
    performance_trend: float  # Performance improvement (negative is slower)


class HistoricalMetrics(BaseModel):
    """Schema for historical metrics data"""
    client_id: int
    workflow_id: Optional[int] = None
    period_type: str  # 'daily', 'weekly', 'monthly'
    start_date: date
    end_date: date
    metrics_data: List[Dict[str, Any]]  # Time series data
    trends: MetricsTrend


class ProductionExecutionFilter(BaseModel):
    """Schema for production execution filtering criteria"""
    exclude_manual: bool = True
    exclude_test_workflows: bool = True
    include_workflow_patterns: Optional[List[str]] = None
    exclude_workflow_patterns: Optional[List[str]] = None