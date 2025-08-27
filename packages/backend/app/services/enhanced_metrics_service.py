"""Enhanced metrics service using persistent data storage"""

from datetime import datetime, date, timedelta, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc, or_
from sqlalchemy.orm import selectinload
import logging

from app.models import (
    Client,
    Workflow,
    WorkflowExecution,
    ExecutionStatus,
    MetricsAggregation,
    AggregationPeriod,
    WorkflowTrendMetrics
)
from app.schemas.metrics import (
    ClientMetrics,
    ClientWorkflowMetrics,
    WorkflowMetrics,
    AdminMetricsResponse,
    HistoricalMetrics,
    MetricsTrend
)
from app.services.cache.redis import redis_client

logger = logging.getLogger(__name__)


class EnhancedMetricsService:
    """Enhanced metrics service using persistent database storage"""
    
    def __init__(self):
        self.cache_ttl = 300  # 5 minutes cache for aggregated data
        
    async def get_client_metrics(
        self, 
        db: AsyncSession, 
        client_id: int,
        use_cache: bool = True
    ) -> ClientMetrics:
        """Get current metrics for a client using persistent data"""
        cache_key = f"enhanced_client_metrics:{client_id}"
        
        if use_cache:
            cached = await redis_client.get(cache_key)
            if cached:
                return ClientMetrics(**cached)
        
        # Get client
        client = await self._get_client_by_id(db, client_id)
        if not client:
            raise ValueError(f"Client {client_id} not found")
        
        # Get recent aggregation or compute from raw data
        recent_metrics = await self._get_recent_client_aggregation(db, client_id)
        
        if recent_metrics:
            # Use aggregated data
            metrics = ClientMetrics(
                client_id=client.id,
                client_name=client.name,
                total_workflows=recent_metrics.total_workflows or 0,
                active_workflows=recent_metrics.active_workflows or 0,
                total_executions=recent_metrics.total_executions,
                successful_executions=recent_metrics.successful_executions,
                failed_executions=recent_metrics.failed_executions,
                success_rate=recent_metrics.success_rate,
                avg_execution_time=recent_metrics.avg_execution_time_seconds,
                last_activity=await self._get_last_activity(db, client_id),
                time_saved_hours=recent_metrics.time_saved_hours,
                last_updated=recent_metrics.computed_at  # Add timestamp from aggregation
            )
        else:
            # Fallback to computing from raw data
            metrics = await self._compute_client_metrics_from_raw_data(db, client)
        
        # Cache the result
        if use_cache:
            await redis_client.set(cache_key, metrics.model_dump(), expire=self.cache_ttl)
        
        return metrics
    
    async def get_historical_metrics(
        self,
        db: AsyncSession,
        client_id: int,
        period_type: AggregationPeriod,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        workflow_id: Optional[int] = None
    ) -> HistoricalMetrics:
        """Get historical metrics for a client or specific workflow"""
        
        # Default to last 30 days if no dates provided
        if not end_date:
            end_date = datetime.utcnow().date()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Build query for aggregations
        query = select(MetricsAggregation).where(
            and_(
                MetricsAggregation.client_id == client_id,
                MetricsAggregation.period_type == period_type,
                MetricsAggregation.period_start >= start_date,
                MetricsAggregation.period_start <= end_date
            )
        )
        
        if workflow_id:
            query = query.where(MetricsAggregation.workflow_id == workflow_id)
        else:
            # Only client-wide aggregations
            query = query.where(MetricsAggregation.workflow_id.is_(None))
        
        query = query.order_by(MetricsAggregation.period_start)
        
        result = await db.execute(query)
        aggregations = result.scalars().all()
        
        # Convert to historical metrics format
        metrics_data = []
        for agg in aggregations:
            metrics_data.append({
                "date": agg.period_start.isoformat(),
                "total_executions": agg.total_executions,
                "successful_executions": agg.successful_executions,
                "failed_executions": agg.failed_executions,
                "success_rate": agg.success_rate,
                "avg_execution_time": agg.avg_execution_time_seconds,
                "time_saved_hours": agg.time_saved_hours,
                "productivity_score": agg.productivity_score
            })
        
        # Calculate trends
        trends = await self._calculate_trends(aggregations)
        
        return HistoricalMetrics(
            client_id=client_id,
            workflow_id=workflow_id,
            period_type=period_type.value,
            start_date=start_date,
            end_date=end_date,
            metrics_data=metrics_data,
            trends=trends
        )
    
    async def get_client_workflow_metrics(
        self,
        db: AsyncSession,
        client_id: int
    ) -> ClientWorkflowMetrics:
        """Get workflow-level metrics for a client"""
        client = await self._get_client_by_id(db, client_id)
        if not client:
            raise ValueError(f"Client {client_id} not found")
        
        # Get client summary
        client_summary = await self.get_client_metrics(db, client_id)
        
        # Get workflows with recent executions
        workflows_query = select(Workflow).where(
            Workflow.client_id == client_id
        ).options(
            selectinload(Workflow.executions)
        )
        
        workflows_result = await db.execute(workflows_query)
        workflows = workflows_result.scalars().all()
        
        workflow_metrics = []
        for workflow in workflows:
            # Get recent executions (last 7 days)
            recent_date = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(days=7)
            recent_executions = [
                e for e in workflow.executions 
                if e.is_production and e.started_at and e.started_at > recent_date
            ]
            
            total_executions = len(recent_executions)
            successful = len([e for e in recent_executions if e.is_successful])
            failed = len([e for e in recent_executions if e.is_failed])
            
            success_rate = (successful / total_executions * 100) if total_executions > 0 else 0.0
            
            # Calculate average execution time
            execution_times = [e.duration_seconds for e in recent_executions if e.duration_seconds]
            avg_time = sum(execution_times) / len(execution_times) if execution_times else None
            
            # Get last execution
            last_execution = None
            if recent_executions:
                last_exec = max(recent_executions, key=lambda x: x.started_at or datetime.min.replace(tzinfo=timezone.utc))
                last_execution = last_exec.started_at
            
            # Determine status
            status = 'active' if workflow.active else 'inactive'
            if failed > successful and total_executions > 0:
                status = 'error'
            
            workflow_metrics.append(WorkflowMetrics(
                workflow_id=str(workflow.n8n_workflow_id),
                workflow_name=workflow.name,
                total_executions=total_executions,
                successful_executions=successful,
                failed_executions=failed,
                success_rate=round(success_rate, 2),
                avg_execution_time=round(avg_time, 2) if avg_time else None,
                last_execution=last_execution,
                status=status
            ))
        
        return ClientWorkflowMetrics(
            client_id=client.id,
            client_name=client.name,
            workflows=workflow_metrics,
            summary=client_summary
        )
    
    async def get_admin_metrics(self, db: AsyncSession) -> AdminMetricsResponse:
        """Get admin view of all client metrics"""
        # Get all clients
        clients_query = select(Client)
        clients_result = await db.execute(clients_query)
        clients = clients_result.scalars().all()
        
        client_metrics = []
        total_workflows = 0
        total_executions = 0
        total_successful = 0
        total_time_saved = 0.0
        
        for client in clients:
            try:
                metrics = await self.get_client_metrics(db, client.id, use_cache=False)
                client_metrics.append(metrics)
                total_workflows += metrics.total_workflows
                total_executions += metrics.total_executions
                total_successful += metrics.successful_executions
                if metrics.time_saved_hours:
                    total_time_saved += metrics.time_saved_hours
            except Exception as e:
                logger.error(f"Error getting metrics for client {client.id}: {e}")
                # Add empty metrics for failed clients
                client_metrics.append(ClientMetrics(
                    client_id=client.id,
                    client_name=client.name,
                    total_workflows=0,
                    active_workflows=0,
                    total_executions=0,
                    successful_executions=0,
                    failed_executions=0,
                    success_rate=0.0,
                    avg_execution_time=None,
                    last_activity=None,
                    time_saved_hours=None,
                    last_updated=None  # No update time for failed clients
                ))
        
        overall_success_rate = (total_successful / total_executions * 100) if total_executions > 0 else 0.0
        
        # Get the most recent update timestamp across all clients
        last_updated = None
        if client_metrics:
            # First try to get from client-specific last_updated timestamps
            client_update_times = [c.last_updated for c in client_metrics if c.last_updated]
            if client_update_times:
                # Ensure all timestamps are timezone-aware for comparison
                from datetime import timezone
                normalized_times = []
                for dt in client_update_times:
                    if dt.tzinfo is None:
                        # Make timezone-naive datetime timezone-aware (assume UTC)
                        dt = dt.replace(tzinfo=timezone.utc)
                    normalized_times.append(dt)
                last_updated = max(normalized_times)
            
            # If no aggregation timestamps, get the most recent sync timestamp from raw data
            if not last_updated:
                # Get the most recent last_synced_at from any workflow execution
                sync_stmt = select(func.max(WorkflowExecution.last_synced_at))
                sync_result = await db.execute(sync_stmt)
                sync_timestamp = sync_result.scalar_one_or_none()
                if sync_timestamp:
                    last_updated = sync_timestamp
        
        return AdminMetricsResponse(
            clients=client_metrics,
            total_clients=len(client_metrics),
            total_workflows=total_workflows,
            total_executions=total_executions,
            overall_success_rate=round(overall_success_rate, 2),
            total_time_saved_hours=round(total_time_saved, 1) if total_time_saved > 0 else None,
            last_updated=last_updated
        )
    
    async def _get_client_by_id(self, db: AsyncSession, client_id: int) -> Optional[Client]:
        """Get client by ID"""
        stmt = select(Client).where(Client.id == client_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _get_recent_client_aggregation(
        self, 
        db: AsyncSession, 
        client_id: int
    ) -> Optional[MetricsAggregation]:
        """Get the most recent daily aggregation for a client"""
        stmt = select(MetricsAggregation).where(
            and_(
                MetricsAggregation.client_id == client_id,
                MetricsAggregation.workflow_id.is_(None),  # Client-wide aggregation
                MetricsAggregation.period_type == AggregationPeriod.DAILY
            )
        ).order_by(desc(MetricsAggregation.period_start)).limit(1)
        
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _get_last_activity(self, db: AsyncSession, client_id: int) -> Optional[datetime]:
        """Get last activity timestamp for a client"""
        stmt = select(func.max(WorkflowExecution.started_at)).where(
            and_(
                WorkflowExecution.client_id == client_id,
                WorkflowExecution.is_production == True
            )
        )
        
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _compute_client_metrics_from_raw_data(
        self, 
        db: AsyncSession, 
        client: Client
    ) -> ClientMetrics:
        """Compute metrics from raw execution data as fallback"""
        # Get workflows count
        workflows_stmt = select(func.count(Workflow.id), func.count().filter(Workflow.active == True)).where(
            Workflow.client_id == client.id
        )
        workflows_result = await db.execute(workflows_stmt)
        total_workflows, active_workflows = workflows_result.one()
        
        # Get recent executions (last 7 days)
        recent_date = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(days=7)
        executions_stmt = select(WorkflowExecution).where(
            and_(
                WorkflowExecution.client_id == client.id,
                WorkflowExecution.is_production == True,
                WorkflowExecution.started_at >= recent_date
            )
        )
        
        executions_result = await db.execute(executions_stmt)
        executions = executions_result.scalars().all()
        
        total_executions = len(executions)
        successful = len([e for e in executions if e.is_successful])
        failed = len([e for e in executions if e.is_failed])
        
        success_rate = (successful / total_executions * 100) if total_executions > 0 else 0.0
        
        # Calculate average execution time
        execution_times = [e.duration_seconds for e in executions if e.duration_seconds]
        avg_time = sum(execution_times) / len(execution_times) if execution_times else None
        
        # Get last activity
        last_activity = None
        if executions:
            last_exec = max(executions, key=lambda x: x.started_at or datetime.min.replace(tzinfo=timezone.utc))
            last_activity = last_exec.started_at
        
        # Get the most recent sync timestamp for this client
        sync_stmt = select(func.max(WorkflowExecution.last_synced_at)).where(
            WorkflowExecution.client_id == client.id
        )
        sync_result = await db.execute(sync_stmt)
        last_sync_time = sync_result.scalar_one_or_none()
        
        # Calculate time saved (estimate 30 minutes per successful execution)
        time_saved_hours = round(successful * 0.5, 1) if successful > 0 else None
        
        return ClientMetrics(
            client_id=client.id,
            client_name=client.name,
            total_workflows=total_workflows or 0,
            active_workflows=active_workflows or 0,
            total_executions=total_executions,
            successful_executions=successful,
            failed_executions=failed,
            success_rate=round(success_rate, 2),
            avg_execution_time=round(avg_time, 2) if avg_time else None,
            last_activity=last_activity,
            time_saved_hours=time_saved_hours,
            last_updated=last_sync_time or datetime.utcnow()  # Use sync time or current time
        )
    
    async def _calculate_trends(self, aggregations: List[MetricsAggregation]) -> MetricsTrend:
        """Calculate trend indicators from aggregation data"""
        if len(aggregations) < 2:
            return MetricsTrend(
                execution_trend=0.0,
                success_rate_trend=0.0,
                performance_trend=0.0
            )
        
        recent = aggregations[-1]
        previous = aggregations[-2]
        
        # Calculate trends as percentage change
        execution_trend = 0.0
        if previous.total_executions > 0:
            execution_trend = ((recent.total_executions - previous.total_executions) / previous.total_executions) * 100
        
        success_rate_trend = recent.success_rate - previous.success_rate
        
        performance_trend = 0.0
        if previous.avg_execution_time_seconds and recent.avg_execution_time_seconds:
            performance_trend = ((previous.avg_execution_time_seconds - recent.avg_execution_time_seconds) / previous.avg_execution_time_seconds) * 100
        
        return MetricsTrend(
            execution_trend=round(execution_trend, 2),
            success_rate_trend=round(success_rate_trend, 2),
            performance_trend=round(performance_trend, 2)
        )


# Global service instance
enhanced_metrics_service = EnhancedMetricsService()