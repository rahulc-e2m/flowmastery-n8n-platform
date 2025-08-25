"""Metrics schemas"""

from datetime import datetime
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


class MetricsError(BaseModel):
    """Schema for metrics error response"""
    error: str
    client_id: int
    client_name: str
    details: Optional[str] = None