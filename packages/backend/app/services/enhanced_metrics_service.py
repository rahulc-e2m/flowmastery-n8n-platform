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
        self.cache_ttl = 900  # 15 minutes cache to match Celery schedule
        
    async def get_client_metrics(
        self, 
        db: AsyncSession, 
        client_id: int,
        use_cache: bool = True
    ) -> ClientMetrics:
        """Get current metrics for a client using persistent data.
        IMPORTANT: totals are computed from raw execution data (all-time),
        while trends use recent aggregations when available.
        """
        cache_key = f"enhanced_client_metrics:{client_id}"
        
        if use_cache:
            cached = await redis_client.get(cache_key)
            if cached:
                return ClientMetrics(**cached)
        
        # Get client
        client = await self._get_client_by_id(db, client_id)
        if not client:
            raise ValueError(f"Client {client_id} not found")
        
        # Get recent aggregation (for timestamp only) and trends
        recent_metrics = await self._get_recent_client_aggregation(db, client_id)
        trends = await self._calculate_client_trends(db, client_id)
        
        # Compute all-time summary from raw data
        summary = await self._get_all_time_client_summary(db, client_id)
        all_time_saved_hours = await self._calculate_all_time_saved(db, client_id)
        last_activity = await self._get_last_activity(db, client_id)
        
        metrics = ClientMetrics(
            client_id=client.id,
            client_name=client.name,
            total_workflows=summary.get('total_workflows', 0),
            active_workflows=summary.get('active_workflows', 0),
            total_executions=summary.get('total_executions', 0),
            successful_executions=summary.get('successful_executions', 0),
            failed_executions=summary.get('failed_executions', 0),
            success_rate=round(summary.get('success_rate', 0.0), 1),
            avg_execution_time=summary.get('avg_execution_time', None),
            last_activity=last_activity,
            time_saved_hours=all_time_saved_hours,
            last_updated=await self._get_last_sync_time(db, client_id),
            trends=trends
        )
        
        # Cache the result with extended TTL if data is fresh
        if use_cache:
            cache_ttl = self.cache_ttl
            if recent_metrics and recent_metrics.computed_at:
                age_minutes = (datetime.utcnow().replace(tzinfo=timezone.utc) - recent_metrics.computed_at).total_seconds() / 60
                if age_minutes < 5:
                    cache_ttl = self.cache_ttl * 2
            await redis_client.set(cache_key, metrics.model_dump(), expire=cache_ttl)
        
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
            # Get recent executions (last 30 days for better time saved calculation)
            recent_date = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(days=30)
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
            
            # Compute time saved for this workflow (last 30 days)
            minutes_per_success = workflow.time_saved_per_execution_minutes if workflow.time_saved_per_execution_minutes is not None else 30
            time_saved_hours = round((successful * minutes_per_success) / 60, 2) if successful > 0 else 0.0

            workflow_metrics.append(WorkflowMetrics(
                workflow_id=str(workflow.n8n_workflow_id),
                workflow_name=workflow.name,
                total_executions=total_executions,
                successful_executions=successful,
                failed_executions=failed,
                success_rate=round(success_rate, 2),
                avg_execution_time=round(avg_time, 2) if avg_time else None,
                last_execution=last_execution,
                status=status,
                time_saved_per_execution_minutes=minutes_per_success,
                time_saved_hours=time_saved_hours
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
        
        overall_success_rate = round((total_successful / total_executions * 100), 1) if total_executions > 0 else 0.0
        
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
        
        # Calculate overall system trends
        overall_trends = await self._calculate_overall_trends(db)
        
        return AdminMetricsResponse(
            clients=client_metrics,
            total_clients=len(client_metrics),
            total_workflows=total_workflows,
            total_executions=total_executions,
            overall_success_rate=round(overall_success_rate, 2),
            total_time_saved_hours=round(total_time_saved, 1) if total_time_saved > 0 else None,
            last_updated=last_updated,
            trends=overall_trends
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
    
    async def _calculate_all_time_saved(self, db: AsyncSession, client_id: int) -> Optional[float]:
        """Calculate all-time time saved for a client from all successful executions"""
        # Get all successful executions for this client
        executions_stmt = select(WorkflowExecution).where(
            and_(
                WorkflowExecution.client_id == client_id,
                WorkflowExecution.is_production == True,
                WorkflowExecution.status == ExecutionStatus.SUCCESS  # Use status column directly
            )
        )
        
        executions_result = await db.execute(executions_stmt)
        successful_executions = executions_result.scalars().all()
        
        if not successful_executions:
            return None
        
        # Get per-workflow time saved minutes for this client
        workflows_minutes_stmt = select(Workflow.id, Workflow.time_saved_per_execution_minutes).where(
            Workflow.client_id == client_id
        )
        workflows_minutes_result = await db.execute(workflows_minutes_stmt)
        workflow_minutes = {wid: (mins if mins is not None else 30) for wid, mins in workflows_minutes_result.all()}

        # Calculate total minutes saved across all successful executions
        total_minutes_saved = 0
        for execution in successful_executions:
            minutes = workflow_minutes.get(execution.workflow_id, 30)
            total_minutes_saved += minutes
        
        return round(total_minutes_saved / 60, 1) if total_minutes_saved > 0 else None

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
        
        # Get recent executions (last 30 days for metrics like success rate and avg time)
        recent_date = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(days=30)
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
        
        # Calculate all-time time saved (not just recent executions)
        time_saved_hours = await self._calculate_all_time_saved(db, client.id)
        
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
            last_updated=last_sync_time or datetime.utcnow(),  # Use sync time or current time
            trends=None  # Will be set by caller
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
        
        # Calculate trends as percentage change with bounds
        execution_trend = 0.0
        
        # For execution trend, handle edge cases
        if previous.total_executions == 0 and recent.total_executions > 0:
            # From 0 to something, show 100% increase (capped)
            execution_trend = 100.0
        elif previous.total_executions > 0:
            # Normal percentage calculation
            execution_trend = ((recent.total_executions - previous.total_executions) / previous.total_executions) * 100
            # Cap extreme values to +/- 500%
            execution_trend = max(-100.0, min(500.0, execution_trend))
        
        # Success rate trend is already a percentage point difference (not percentage change)
        success_rate_trend = recent.success_rate - previous.success_rate
        # Cap to reasonable range (-100 to +100 percentage points)
        success_rate_trend = max(-100.0, min(100.0, success_rate_trend))
        
        # Performance trend (positive means improvement - faster execution)
        performance_trend = 0.0
        if previous.avg_execution_time_seconds and recent.avg_execution_time_seconds:
            if previous.avg_execution_time_seconds > 0:
                performance_trend = ((previous.avg_execution_time_seconds - recent.avg_execution_time_seconds) / previous.avg_execution_time_seconds) * 100
                # Cap to reasonable range
                performance_trend = max(-100.0, min(100.0, performance_trend))
        
        return MetricsTrend(
            execution_trend=round(execution_trend, 1),
            success_rate_trend=round(success_rate_trend, 1),
            performance_trend=round(performance_trend, 1)
        )
    
    async def _calculate_client_trends(self, db: AsyncSession, client_id: int) -> Optional[MetricsTrend]:
        """Calculate trend indicators for a specific client based on all-time cumulative data"""
        try:
            # Calculate trends from cumulative all-time data over meaningful periods
            # Compare last 30 days vs previous 30 days to show growth in all-time totals
            return await self._calculate_trends_from_cumulative_data(db, client_id)
            
        except Exception as e:
            logger.warning(f"Failed to calculate trends for client {client_id}: {e}")
            return MetricsTrend(execution_trend=0.0, success_rate_trend=0.0, performance_trend=0.0)
    
    async def _calculate_overall_trends(self, db: AsyncSession) -> Optional[MetricsTrend]:
        """Calculate overall system trends across all clients using cumulative all-time data"""
        try:
            # Compare cumulative all-time totals: up to 30 days ago vs up to now
            # This shows how the overall system has grown over the last 30 days
            now = datetime.utcnow().replace(tzinfo=timezone.utc)
            cutoff_30_days = now - timedelta(days=30)
            
            # Get all-time totals up to 30 days ago (previous period baseline)
            previous_stmt = select(WorkflowExecution).where(
                and_(
                    WorkflowExecution.is_production == True,
                    WorkflowExecution.started_at < cutoff_30_days
                )
            )
            
            previous_result = await db.execute(previous_stmt)
            previous_executions = previous_result.scalars().all()
            
            # Get all-time totals up to now (current period)
            current_stmt = select(WorkflowExecution).where(
                WorkflowExecution.is_production == True
            )
            
            current_result = await db.execute(current_stmt)
            current_executions = current_result.scalars().all()
            
            # Calculate cumulative metrics for both periods
            previous_total = len(previous_executions)
            previous_successful = len([e for e in previous_executions if e.is_successful])
            previous_times = [e.duration_seconds for e in previous_executions if e.duration_seconds]
            previous_avg_time = sum(previous_times) / len(previous_times) if previous_times else 0
            
            current_total = len(current_executions)
            current_successful = len([e for e in current_executions if e.is_successful])
            current_times = [e.duration_seconds for e in current_executions if e.duration_seconds]
            current_avg_time = sum(current_times) / len(current_times) if current_times else 0
            
            if current_total == 0:
                return MetricsTrend(execution_trend=0.0, success_rate_trend=0.0, performance_trend=0.0)
            
            # Calculate execution trend showing growth in all-time totals
            execution_trend = 0.0
            if previous_total == 0 and current_total > 0:
                execution_trend = 100.0
            elif previous_total > 0:
                execution_trend = ((current_total - previous_total) / previous_total) * 100
                execution_trend = max(-100.0, min(500.0, execution_trend))
            
            # Calculate success rate trend (change in overall success rate)
            current_success_rate = (current_successful / current_total * 100) if current_total > 0 else 0
            previous_success_rate = (previous_successful / previous_total * 100) if previous_total > 0 else 0
            success_rate_trend = current_success_rate - previous_success_rate
            success_rate_trend = max(-100.0, min(100.0, success_rate_trend))
            
            # Calculate performance trend (improvement in execution time)
            performance_trend = 0.0
            if previous_avg_time > 0 and current_avg_time > 0:
                performance_trend = ((previous_avg_time - current_avg_time) / previous_avg_time) * 100
                performance_trend = max(-100.0, min(100.0, performance_trend))
            
            return MetricsTrend(
                execution_trend=round(execution_trend, 1),
                success_rate_trend=round(success_rate_trend, 1),
                performance_trend=round(performance_trend, 1)
            )
            
        except Exception as e:
            logger.warning(f"Failed to calculate overall trends: {e}")
            return MetricsTrend(execution_trend=0.0, success_rate_trend=0.0, performance_trend=0.0)
    
    async def _calculate_trends_from_cumulative_data(self, db: AsyncSession, client_id: int) -> MetricsTrend:
        """Calculate trends from cumulative all-time data comparing meaningful periods"""
        try:
            # Compare cumulative totals: all data up to 30 days ago vs all data up to 60 days ago
            # This shows how the all-time totals have grown over the last 30 days
            now = datetime.utcnow().replace(tzinfo=timezone.utc)
            cutoff_30_days = now - timedelta(days=30)
            cutoff_60_days = now - timedelta(days=60)
            
            # Get all-time totals up to 30 days ago (previous period baseline)
            previous_stmt = select(WorkflowExecution).where(
                and_(
                    WorkflowExecution.client_id == client_id,
                    WorkflowExecution.is_production == True,
                    WorkflowExecution.started_at < cutoff_30_days
                )
            )
            
            previous_result = await db.execute(previous_stmt)
            previous_executions = previous_result.scalars().all()
            
            # Get all-time totals up to now (current period)
            current_stmt = select(WorkflowExecution).where(
                and_(
                    WorkflowExecution.client_id == client_id,
                    WorkflowExecution.is_production == True
                )
            )
            
            current_result = await db.execute(current_stmt)
            current_executions = current_result.scalars().all()
            
            # Calculate cumulative metrics for both periods
            previous_total = len(previous_executions)
            previous_successful = len([e for e in previous_executions if e.is_successful])
            previous_times = [e.duration_seconds for e in previous_executions if e.duration_seconds]
            previous_avg_time = sum(previous_times) / len(previous_times) if previous_times else 0
            
            current_total = len(current_executions)
            current_successful = len([e for e in current_executions if e.is_successful])
            current_times = [e.duration_seconds for e in current_executions if e.duration_seconds]
            current_avg_time = sum(current_times) / len(current_times) if current_times else 0
            
            # Calculate trends showing growth in all-time totals
            execution_trend = 0.0
            if previous_total == 0 and current_total > 0:
                execution_trend = 100.0
            elif previous_total > 0:
                execution_trend = ((current_total - previous_total) / previous_total) * 100
                execution_trend = max(-100.0, min(500.0, execution_trend))
            elif current_total == 0 and previous_total > 0:
                execution_trend = -100.0
            
            # Success rate trend (change in overall success rate)
            current_success_rate = (current_successful / current_total * 100) if current_total > 0 else 0
            previous_success_rate = (previous_successful / previous_total * 100) if previous_total > 0 else 0
            success_rate_trend = current_success_rate - previous_success_rate
            success_rate_trend = max(-100.0, min(100.0, success_rate_trend))
            
            # Performance trend (improvement in average execution time)
            performance_trend = 0.0
            if previous_avg_time > 0 and current_avg_time > 0:
                performance_trend = ((previous_avg_time - current_avg_time) / previous_avg_time) * 100
                performance_trend = max(-100.0, min(100.0, performance_trend))
            
            return MetricsTrend(
                execution_trend=round(execution_trend, 1),
                success_rate_trend=round(success_rate_trend, 1),
                performance_trend=round(performance_trend, 1)
            )
            
        except Exception as e:
            logger.warning(f"Failed to calculate trends from cumulative data for client {client_id}: {e}")
            return MetricsTrend(execution_trend=0.0, success_rate_trend=0.0, performance_trend=0.0)
    
    async def _get_last_sync_time(self, db: AsyncSession, client_id: int) -> Optional[datetime]:
        """Get the most recent last_synced_at timestamp for a client's executions"""
        stmt = select(func.max(WorkflowExecution.last_synced_at)).where(
            WorkflowExecution.client_id == client_id
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_all_time_client_summary(self, db: AsyncSession, client_id: int) -> Dict[str, Any]:
        """Compute all-time summary metrics for a client from raw executions"""
        # Workflows counts
        workflows_stmt = select(
            func.count(Workflow.id).label('total_workflows'),
            func.count().filter(Workflow.active == True).label('active_workflows')
        ).where(Workflow.client_id == client_id)
        wf_res = await db.execute(workflows_stmt)
        total_workflows, active_workflows = wf_res.one()

        # Executions counts
        total_exec_stmt = select(func.count(WorkflowExecution.id)).where(
            WorkflowExecution.client_id == client_id,
            WorkflowExecution.is_production == True
        )
        success_stmt = select(func.count(WorkflowExecution.id)).where(
            WorkflowExecution.client_id == client_id,
            WorkflowExecution.is_production == True,
            WorkflowExecution.status == ExecutionStatus.SUCCESS
        )
        failed_stmt = select(func.count(WorkflowExecution.id)).where(
            WorkflowExecution.client_id == client_id,
            WorkflowExecution.is_production == True,
            WorkflowExecution.status == ExecutionStatus.ERROR
        )

        total_executions = (await db.execute(total_exec_stmt)).scalar_one() or 0
        successful = (await db.execute(success_stmt)).scalar_one() or 0
        failed = (await db.execute(failed_stmt)).scalar_one() or 0

        success_rate = round((successful / total_executions * 100), 1) if total_executions > 0 else 0.0

        # Average execution time over last 30 days for better signal
        recent_date = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(days=30)
        avg_time_stmt = select(func.avg(WorkflowExecution.execution_time_ms)).where(
            WorkflowExecution.client_id == client_id,
            WorkflowExecution.is_production == True,
            WorkflowExecution.execution_time_ms.isnot(None),
            WorkflowExecution.started_at >= recent_date
        )
        avg_ms = (await db.execute(avg_time_stmt)).scalar_one_or_none()
        avg_seconds = float(avg_ms) / 1000.0 if avg_ms else None

        return {
            'total_workflows': total_workflows or 0,
            'active_workflows': active_workflows or 0,
            'total_executions': total_executions,
            'successful_executions': successful,
            'failed_executions': failed,
            'success_rate': success_rate,
            'avg_execution_time': round(avg_seconds, 2) if avg_seconds else None,
        }


# Global service instance
enhanced_metrics_service = EnhancedMetricsService()
