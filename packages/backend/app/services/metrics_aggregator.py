"""Metrics aggregation service for computing historical statistics"""

import logging
from datetime import datetime, date, timedelta, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func, desc, delete
from collections import Counter

from app.models import (
    Client,
    Workflow,
    WorkflowExecution,
    ExecutionStatus,
    MetricsAggregation,
    AggregationPeriod,
    WorkflowTrendMetrics
)

logger = logging.getLogger(__name__)


class MetricsAggregator:
    """Service for computing and storing metrics aggregations"""
    
    def __init__(self):
        self.logger = logger
    
    async def compute_daily_aggregations(
        self, 
        db: AsyncSession, 
        target_date: date
    ) -> Dict[str, Any]:
        """Compute daily aggregations for all clients and workflows"""
        results = {"aggregations_created": 0, "errors": [], "processed_clients": 0}
        
        # Get all clients
        clients_stmt = select(Client)
        clients_result = await db.execute(clients_stmt)
        clients = clients_result.scalars().all()
        
        for client in clients:
            try:
                results["processed_clients"] += 1
                
                # Client-wide aggregation
                client_agg = await self._compute_client_daily_aggregation(db, client.id, target_date)
                if client_agg:
                    results["aggregations_created"] += 1
                
                # Workflow-specific aggregations
                workflow_aggs = await self._compute_workflow_daily_aggregations(db, client.id, target_date)
                results["aggregations_created"] += len(workflow_aggs)
                
            except Exception as e:
                error_msg = f"Error computing daily aggregations for client {client.id}: {e}"
                self.logger.error(error_msg)
                results["errors"].append(error_msg)
        
        results["total_aggregations"] = results["aggregations_created"]
        return results
    
    async def compute_weekly_aggregations(
        self,
        db: AsyncSession,
        week_start: date
    ) -> Dict[str, Any]:
        """Compute weekly aggregations"""
        results = {"aggregations_created": 0, "errors": [], "processed_clients": 0}
        
        # Calculate week end (Sunday)
        week_end = week_start + timedelta(days=6)
        
        clients_stmt = select(Client)
        clients_result = await db.execute(clients_stmt)
        clients = clients_result.scalars().all()
        
        for client in clients:
            try:
                results["processed_clients"] += 1
                
                # Client-wide weekly aggregation
                client_agg = await self._compute_period_aggregation(
                    db, client.id, week_start, week_end, AggregationPeriod.WEEKLY
                )
                if client_agg:
                    results["aggregations_created"] += 1
                
                # Workflow-specific weekly aggregations
                workflow_aggs = await self._compute_workflow_period_aggregations(
                    db, client.id, week_start, week_end, AggregationPeriod.WEEKLY
                )
                results["aggregations_created"] += len(workflow_aggs)
                
            except Exception as e:
                error_msg = f"Error computing weekly aggregations for client {client.id}: {e}"
                self.logger.error(error_msg)
                results["errors"].append(error_msg)
        
        results["total_aggregations"] = results["aggregations_created"]
        return results
    
    async def compute_monthly_aggregations(
        self,
        db: AsyncSession,
        month_start: date
    ) -> Dict[str, Any]:
        """Compute monthly aggregations"""
        results = {"aggregations_created": 0, "errors": [], "processed_clients": 0}
        
        # Calculate month end
        if month_start.month == 12:
            month_end = date(month_start.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(month_start.year, month_start.month + 1, 1) - timedelta(days=1)
        
        clients_stmt = select(Client)
        clients_result = await db.execute(clients_stmt)
        clients = clients_result.scalars().all()
        
        for client in clients:
            try:
                results["processed_clients"] += 1
                
                # Client-wide monthly aggregation
                client_agg = await self._compute_period_aggregation(
                    db, client.id, month_start, month_end, AggregationPeriod.MONTHLY
                )
                if client_agg:
                    results["aggregations_created"] += 1
                
                # Workflow-specific monthly aggregations
                workflow_aggs = await self._compute_workflow_period_aggregations(
                    db, client.id, month_start, month_end, AggregationPeriod.MONTHLY
                )
                results["aggregations_created"] += len(workflow_aggs)
                
            except Exception as e:
                error_msg = f"Error computing monthly aggregations for client {client.id}: {e}"
                self.logger.error(error_msg)
                results["errors"].append(error_msg)
        
        results["total_aggregations"] = results["aggregations_created"]
        return results
    
    async def _compute_client_daily_aggregation(
        self,
        db: AsyncSession,
        client_id: int,
        target_date: date
    ) -> Optional[MetricsAggregation]:
        """Compute daily aggregation for a specific client"""
        return await self._compute_period_aggregation(
            db, client_id, target_date, target_date, AggregationPeriod.DAILY
        )
    
    async def _compute_period_aggregation(
        self,
        db: AsyncSession,
        client_id: int,
        start_date: date,
        end_date: date,
        period_type: AggregationPeriod,
        workflow_id: Optional[int] = None
    ) -> Optional[MetricsAggregation]:
        """Compute aggregation for a specific period"""
        
        # Check if aggregation already exists
        existing_stmt = select(MetricsAggregation).where(
            and_(
                MetricsAggregation.client_id == client_id,
                MetricsAggregation.workflow_id == workflow_id,
                MetricsAggregation.period_type == period_type,
                MetricsAggregation.period_start == start_date,
                MetricsAggregation.period_end == end_date
            )
        )
        existing_result = await db.execute(existing_stmt)
        existing_agg = existing_result.scalar_one_or_none()
        
        # Base query for executions in the period
        executions_query = select(WorkflowExecution).where(
            and_(
                WorkflowExecution.client_id == client_id,
                WorkflowExecution.is_production == True,
                WorkflowExecution.started_at >= datetime.combine(start_date, datetime.min.time()),
                WorkflowExecution.started_at < datetime.combine(end_date + timedelta(days=1), datetime.min.time())
            )
        )
        
        if workflow_id:
            executions_query = executions_query.where(WorkflowExecution.workflow_id == workflow_id)
        
        executions_result = await db.execute(executions_query)
        executions = executions_result.scalars().all()
        
        if not executions:
            # No new executions found for this period
            if existing_agg:
                # Keep existing aggregation, just update the computed_at timestamp
                existing_agg.computed_at = datetime.now(timezone.utc)
                await db.commit()
                return existing_agg
            return None  # No data to aggregate at all
        
        # Compute metrics
        total_executions = len(executions)
        successful_executions = len([e for e in executions if e.status == ExecutionStatus.SUCCESS])
        failed_executions = len([e for e in executions if e.status == ExecutionStatus.ERROR])
        canceled_executions = len([e for e in executions if e.status == ExecutionStatus.CANCELED])
        
        success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0.0
        
        # Calculate execution times
        execution_times = []
        data_sizes = []
        errors = []
        
        for execution in executions:
            if execution.duration_seconds is not None:
                execution_times.append(execution.duration_seconds)
            
            if execution.data_size_bytes is not None:
                data_sizes.append(execution.data_size_bytes)
            
            if execution.error_message:
                errors.append(execution.error_message[:200])  # Truncate for analysis
        
        # Performance metrics
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else None
        min_execution_time = min(execution_times) if execution_times else None
        max_execution_time = max(execution_times) if execution_times else None
        
        # Data metrics
        total_data_size = sum(data_sizes) if data_sizes else None
        avg_data_size = total_data_size / len(data_sizes) if data_sizes else None
        
        # Error analysis
        most_common_error = None
        if errors:
            error_counter = Counter(errors)
            most_common_error = error_counter.most_common(1)[0][0]
        
        # Workflow count (for client-wide aggregations)
        total_workflows = None
        active_workflows = None
        if not workflow_id:
            workflows_stmt = select(Workflow).where(Workflow.client_id == client_id)
            workflows_result = await db.execute(workflows_stmt)
            workflows = workflows_result.scalars().all()
            
            total_workflows = len(workflows)
            active_workflows = len([w for w in workflows if w.active])
        
        # Compute derived metrics
        # Calculate time saved using actual per-workflow minutes
        if workflow_id:
            # For workflow-specific aggregation, get the specific workflow's minutes
            workflow_stmt = select(Workflow.time_saved_per_execution_minutes).where(Workflow.id == workflow_id)
            workflow_result = await db.execute(workflow_stmt)
            minutes_per_execution = workflow_result.scalar_one_or_none() or 30
            time_saved_hours = successful_executions * (minutes_per_execution / 60)
        else:
            # For client-wide aggregation, calculate based on actual executions and their workflow settings
            # Get successful executions with their workflow IDs
            successful_execs_stmt = select(
                WorkflowExecution.workflow_id,
                func.count(WorkflowExecution.id).label('count')
            ).where(
                and_(
                    WorkflowExecution.client_id == client_id,
                    WorkflowExecution.status == ExecutionStatus.SUCCESS,
                    WorkflowExecution.is_production == True,
                    WorkflowExecution.started_at >= datetime.combine(start_date, datetime.min.time()),
                    WorkflowExecution.started_at < datetime.combine(end_date + timedelta(days=1), datetime.min.time())
                )
            ).group_by(WorkflowExecution.workflow_id)
            
            successful_execs_result = await db.execute(successful_execs_stmt)
            successful_by_workflow = successful_execs_result.all()
            
            # Get workflow minutes for all workflows
            workflow_minutes_stmt = select(Workflow.id, Workflow.time_saved_per_execution_minutes).where(
                Workflow.client_id == client_id
            )
            workflow_minutes_result = await db.execute(workflow_minutes_stmt)
            workflow_minutes = {wid: (mins if mins is not None else 30) for wid, mins in workflow_minutes_result.all()}
            
            # Calculate total time saved
            total_minutes_saved = 0
            for workflow_id_exec, count in successful_by_workflow:
                minutes_per_exec = workflow_minutes.get(workflow_id_exec, 30)
                total_minutes_saved += count * minutes_per_exec
            
            time_saved_hours = total_minutes_saved / 60 if total_minutes_saved > 0 else 0
        
        productivity_score = min(100, success_rate * (total_executions / 10))  # Custom productivity metric
        
        # Create or update aggregation
        if existing_agg:
            # Update existing
            existing_agg.total_executions = total_executions
            existing_agg.successful_executions = successful_executions
            existing_agg.failed_executions = failed_executions
            existing_agg.canceled_executions = canceled_executions
            existing_agg.success_rate = success_rate
            existing_agg.avg_execution_time_seconds = avg_execution_time
            existing_agg.min_execution_time_seconds = min_execution_time
            existing_agg.max_execution_time_seconds = max_execution_time
            existing_agg.total_data_size_bytes = total_data_size
            existing_agg.avg_data_size_bytes = avg_data_size
            existing_agg.total_workflows = total_workflows
            existing_agg.active_workflows = active_workflows
            existing_agg.most_common_error = most_common_error
            existing_agg.error_count = failed_executions
            existing_agg.time_saved_hours = time_saved_hours
            existing_agg.productivity_score = productivity_score
            existing_agg.computed_at = datetime.now(timezone.utc)
            
            aggregation = existing_agg
        else:
            # Create new
            aggregation = MetricsAggregation(
                client_id=client_id,
                workflow_id=workflow_id,
                period_type=period_type,
                period_start=start_date,
                period_end=end_date,
                total_executions=total_executions,
                successful_executions=successful_executions,
                failed_executions=failed_executions,
                canceled_executions=canceled_executions,
                success_rate=success_rate,
                avg_execution_time_seconds=avg_execution_time,
                min_execution_time_seconds=min_execution_time,
                max_execution_time_seconds=max_execution_time,
                total_data_size_bytes=total_data_size,
                avg_data_size_bytes=avg_data_size,
                total_workflows=total_workflows,
                active_workflows=active_workflows,
                most_common_error=most_common_error,
                error_count=failed_executions,
                time_saved_hours=time_saved_hours,
                productivity_score=productivity_score,
                computed_at=datetime.now(timezone.utc)
            )
            
            db.add(aggregation)
        
        await db.commit()
        return aggregation
    
    async def _compute_workflow_daily_aggregations(
        self,
        db: AsyncSession,
        client_id: int,
        target_date: date
    ) -> List[MetricsAggregation]:
        """Compute daily aggregations for all workflows of a client"""
        return await self._compute_workflow_period_aggregations(
            db, client_id, target_date, target_date, AggregationPeriod.DAILY
        )
    
    async def _compute_workflow_period_aggregations(
        self,
        db: AsyncSession,
        client_id: int,
        start_date: date,
        end_date: date,
        period_type: AggregationPeriod
    ) -> List[MetricsAggregation]:
        """Compute period aggregations for all workflows of a client"""
        # Get all workflows for the client
        workflows_stmt = select(Workflow).where(Workflow.client_id == client_id)
        workflows_result = await db.execute(workflows_stmt)
        workflows = workflows_result.scalars().all()
        
        aggregations = []
        for workflow in workflows:
            agg = await self._compute_period_aggregation(
                db, client_id, start_date, end_date, period_type, workflow.id
            )
            if agg:
                aggregations.append(agg)
        
        return aggregations
    
    async def cleanup_old_data(
        self,
        db: AsyncSession,
        raw_execution_retention_days: int = 90,
        aggregation_retention_months: int = 24
    ) -> Dict[str, Any]:
        """Clean up old metrics data based on retention policies"""
        results = {"executions_deleted": 0, "aggregations_deleted": 0, "errors": []}
        
        try:
            # Clean up old raw executions
            execution_cutoff = datetime.now(timezone.utc) - timedelta(days=raw_execution_retention_days)
            
            # Only delete executions that have been aggregated
            # Keep recent executions for real-time queries
            delete_executions_stmt = delete(WorkflowExecution).where(
                and_(
                    WorkflowExecution.created_at < execution_cutoff,
                    WorkflowExecution.started_at < execution_cutoff
                )
            )
            
            executions_result = await db.execute(delete_executions_stmt)
            results["executions_deleted"] = executions_result.rowcount
            
            # Clean up old aggregations (keep longer retention)
            aggregation_cutoff = datetime.now(timezone.utc) - timedelta(days=aggregation_retention_months * 30)
            
            delete_aggregations_stmt = delete(MetricsAggregation).where(
                MetricsAggregation.created_at < aggregation_cutoff
            )
            
            aggregations_result = await db.execute(delete_aggregations_stmt)
            results["aggregations_deleted"] = aggregations_result.rowcount
            
            # Clean up old trend metrics
            delete_trends_stmt = delete(WorkflowTrendMetrics).where(
                WorkflowTrendMetrics.created_at < aggregation_cutoff
            )
            
            trends_result = await db.execute(delete_trends_stmt)
            results["trends_deleted"] = trends_result.rowcount
            
            await db.commit()
            
            self.logger.info(
                f"Cleanup completed: deleted {results['executions_deleted']} executions, "
                f"{results['aggregations_deleted']} aggregations, "
                f"{results['trends_deleted']} trend metrics"
            )
            
        except Exception as e:
            await db.rollback()
            error_msg = f"Error during cleanup: {e}"
            self.logger.error(error_msg)
            results["errors"].append(error_msg)
        
        return results
    
    async def get_aggregation_summary(
        self,
        db: AsyncSession,
        client_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get summary of available aggregations"""
        base_query = select(
            MetricsAggregation.period_type,
            func.count().label('count'),
            func.min(MetricsAggregation.period_start).label('earliest_period'),
            func.max(MetricsAggregation.period_start).label('latest_period')
        )
        
        if client_id:
            base_query = base_query.where(MetricsAggregation.client_id == client_id)
        
        base_query = base_query.group_by(MetricsAggregation.period_type)
        
        result = await db.execute(base_query)
        aggregation_summary = result.all()
        
        summary = {}
        for row in aggregation_summary:
            summary[row.period_type.value] = {
                "count": row.count,
                "earliest_period": row.earliest_period.isoformat() if row.earliest_period else None,
                "latest_period": row.latest_period.isoformat() if row.latest_period else None
            }
        
        return summary
    
    # Synchronous versions for Celery tasks
    def compute_daily_aggregations_sync(
        self, 
        db: Session, 
        target_date: date
    ) -> Dict[str, Any]:
        """Synchronous version of compute_daily_aggregations"""
        results = {"aggregations_created": 0, "errors": [], "processed_clients": 0}
        
        # Get all clients
        clients_stmt = select(Client)
        clients_result = db.execute(clients_stmt)
        clients = clients_result.scalars().all()
        
        for client in clients:
            try:
                results["processed_clients"] += 1
                
                # Client-wide aggregation
                client_agg = self._compute_period_aggregation_sync(db, client.id, target_date, target_date, AggregationPeriod.DAILY)
                if client_agg:
                    results["aggregations_created"] += 1
                
                # Workflow-specific aggregations
                workflow_aggs = self._compute_workflow_period_aggregations_sync(db, client.id, target_date, target_date, AggregationPeriod.DAILY)
                results["aggregations_created"] += len(workflow_aggs)
                
            except Exception as e:
                error_msg = f"Error computing daily aggregations for client {client.id}: {e}"
                self.logger.error(error_msg)
                results["errors"].append(error_msg)
        
        results["total_aggregations"] = results["aggregations_created"]
        return results
    
    def compute_weekly_aggregations_sync(
        self,
        db: Session,
        week_start: date
    ) -> Dict[str, Any]:
        """Synchronous version of compute_weekly_aggregations"""
        results = {"aggregations_created": 0, "errors": [], "processed_clients": 0}
        
        # Calculate week end (Sunday)
        week_end = week_start + timedelta(days=6)
        
        clients_stmt = select(Client)
        clients_result = db.execute(clients_stmt)
        clients = clients_result.scalars().all()
        
        for client in clients:
            try:
                results["processed_clients"] += 1
                
                # Client-wide weekly aggregation
                client_agg = self._compute_period_aggregation_sync(
                    db, client.id, week_start, week_end, AggregationPeriod.WEEKLY
                )
                if client_agg:
                    results["aggregations_created"] += 1
                
                # Workflow-specific weekly aggregations
                workflow_aggs = self._compute_workflow_period_aggregations_sync(
                    db, client.id, week_start, week_end, AggregationPeriod.WEEKLY
                )
                results["aggregations_created"] += len(workflow_aggs)
                
            except Exception as e:
                error_msg = f"Error computing weekly aggregations for client {client.id}: {e}"
                self.logger.error(error_msg)
                results["errors"].append(error_msg)
        
        results["total_aggregations"] = results["aggregations_created"]
        return results
    
    def compute_monthly_aggregations_sync(
        self,
        db: Session,
        month_start: date
    ) -> Dict[str, Any]:
        """Synchronous version of compute_monthly_aggregations"""
        results = {"aggregations_created": 0, "errors": [], "processed_clients": 0}
        
        # Calculate month end
        if month_start.month == 12:
            month_end = date(month_start.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(month_start.year, month_start.month + 1, 1) - timedelta(days=1)
        
        clients_stmt = select(Client)
        clients_result = db.execute(clients_stmt)
        clients = clients_result.scalars().all()
        
        for client in clients:
            try:
                results["processed_clients"] += 1
                
                # Client-wide monthly aggregation
                client_agg = self._compute_period_aggregation_sync(
                    db, client.id, month_start, month_end, AggregationPeriod.MONTHLY
                )
                if client_agg:
                    results["aggregations_created"] += 1
                
                # Workflow-specific monthly aggregations
                workflow_aggs = self._compute_workflow_period_aggregations_sync(
                    db, client.id, month_start, month_end, AggregationPeriod.MONTHLY
                )
                results["aggregations_created"] += len(workflow_aggs)
                
            except Exception as e:
                error_msg = f"Error computing monthly aggregations for client {client.id}: {e}"
                self.logger.error(error_msg)
                results["errors"].append(error_msg)
        
        results["total_aggregations"] = results["aggregations_created"]
        return results
    
    def _compute_period_aggregation_sync(
        self,
        db: Session,
        client_id: int,
        start_date: date,
        end_date: date,
        period_type: AggregationPeriod,
        workflow_id: Optional[int] = None
    ) -> Optional[MetricsAggregation]:
        """Synchronous version of _compute_period_aggregation"""
        
        # Check if aggregation already exists
        existing_stmt = select(MetricsAggregation).where(
            and_(
                MetricsAggregation.client_id == client_id,
                MetricsAggregation.workflow_id == workflow_id,
                MetricsAggregation.period_type == period_type,
                MetricsAggregation.period_start == start_date,
                MetricsAggregation.period_end == end_date
            )
        )
        existing_result = db.execute(existing_stmt)
        existing_agg = existing_result.scalar_one_or_none()
        
        # Base query for executions in the period
        executions_query = select(WorkflowExecution).where(
            and_(
                WorkflowExecution.client_id == client_id,
                WorkflowExecution.is_production == True,
                WorkflowExecution.started_at >= datetime.combine(start_date, datetime.min.time()),
                WorkflowExecution.started_at < datetime.combine(end_date + timedelta(days=1), datetime.min.time())
            )
        )
        
        if workflow_id:
            executions_query = executions_query.where(WorkflowExecution.workflow_id == workflow_id)
        
        executions_result = db.execute(executions_query)
        executions = executions_result.scalars().all()
        
        if not executions:
            # No new executions found for this period
            if existing_agg:
                # Keep existing aggregation, just update the computed_at timestamp
                existing_agg.computed_at = datetime.now(timezone.utc)
                db.commit()
                return existing_agg
            return None  # No data to aggregate at all
        
        # Compute metrics
        total_executions = len(executions)
        successful_executions = len([e for e in executions if e.status == ExecutionStatus.SUCCESS])
        failed_executions = len([e for e in executions if e.status == ExecutionStatus.ERROR])
        canceled_executions = len([e for e in executions if e.status == ExecutionStatus.CANCELED])
        
        success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0.0
        
        # Calculate execution times
        execution_times = []
        data_sizes = []
        errors = []
        
        for execution in executions:
            if execution.duration_seconds is not None:
                execution_times.append(execution.duration_seconds)
            
            if execution.data_size_bytes is not None:
                data_sizes.append(execution.data_size_bytes)
            
            if execution.error_message:
                errors.append(execution.error_message[:200])  # Truncate for analysis
        
        # Performance metrics
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else None
        min_execution_time = min(execution_times) if execution_times else None
        max_execution_time = max(execution_times) if execution_times else None
        
        # Data metrics
        total_data_size = sum(data_sizes) if data_sizes else None
        avg_data_size = total_data_size / len(data_sizes) if data_sizes else None
        
        # Error analysis
        most_common_error = None
        if errors:
            error_counter = Counter(errors)
            most_common_error = error_counter.most_common(1)[0][0]
        
        # Workflow count (for client-wide aggregations)
        total_workflows = None
        active_workflows = None
        if not workflow_id:
            workflows_stmt = select(Workflow).where(Workflow.client_id == client_id)
            workflows_result = db.execute(workflows_stmt)
            workflows = workflows_result.scalars().all()
            
            total_workflows = len(workflows)
            active_workflows = len([w for w in workflows if w.active])
        
        # Compute derived metrics
        # Calculate time saved using actual per-workflow minutes
        if workflow_id:
            # For workflow-specific aggregation, get the specific workflow's minutes
            workflow_stmt = select(Workflow.time_saved_per_execution_minutes).where(Workflow.id == workflow_id)
            workflow_result = db.execute(workflow_stmt)
            minutes_per_execution = workflow_result.scalar_one_or_none() or 30
            time_saved_hours = successful_executions * (minutes_per_execution / 60)
        else:
            # For client-wide aggregation, calculate based on actual executions and their workflow settings
            # Get successful executions with their workflow IDs
            successful_execs_stmt = select(
                WorkflowExecution.workflow_id,
                func.count(WorkflowExecution.id).label('count')
            ).where(
                and_(
                    WorkflowExecution.client_id == client_id,
                    WorkflowExecution.status == ExecutionStatus.SUCCESS,
                    WorkflowExecution.is_production == True,
                    WorkflowExecution.started_at >= datetime.combine(start_date, datetime.min.time()),
                    WorkflowExecution.started_at < datetime.combine(end_date + timedelta(days=1), datetime.min.time())
                )
            ).group_by(WorkflowExecution.workflow_id)
            
            successful_execs_result = db.execute(successful_execs_stmt)
            successful_by_workflow = successful_execs_result.all()
            
            # Get workflow minutes for all workflows
            workflow_minutes_stmt = select(Workflow.id, Workflow.time_saved_per_execution_minutes).where(
                Workflow.client_id == client_id
            )
            workflow_minutes_result = db.execute(workflow_minutes_stmt)
            workflow_minutes = {wid: (mins if mins is not None else 30) for wid, mins in workflow_minutes_result.all()}
            
            # Calculate total time saved
            total_minutes_saved = 0
            for workflow_id_exec, count in successful_by_workflow:
                minutes_per_exec = workflow_minutes.get(workflow_id_exec, 30)
                total_minutes_saved += count * minutes_per_exec
            
            time_saved_hours = total_minutes_saved / 60 if total_minutes_saved > 0 else 0
        
        productivity_score = min(100, success_rate * (total_executions / 10))  # Custom productivity metric
        
        # Create or update aggregation
        if existing_agg:
            # Update existing
            existing_agg.total_executions = total_executions
            existing_agg.successful_executions = successful_executions
            existing_agg.failed_executions = failed_executions
            existing_agg.canceled_executions = canceled_executions
            existing_agg.success_rate = success_rate
            existing_agg.avg_execution_time_seconds = avg_execution_time
            existing_agg.min_execution_time_seconds = min_execution_time
            existing_agg.max_execution_time_seconds = max_execution_time
            existing_agg.total_data_size_bytes = total_data_size
            existing_agg.avg_data_size_bytes = avg_data_size
            existing_agg.total_workflows = total_workflows
            existing_agg.active_workflows = active_workflows
            existing_agg.most_common_error = most_common_error
            existing_agg.error_count = failed_executions
            existing_agg.time_saved_hours = time_saved_hours
            existing_agg.productivity_score = productivity_score
            existing_agg.computed_at = datetime.now(timezone.utc)
            
            aggregation = existing_agg
        else:
            # Create new
            aggregation = MetricsAggregation(
                client_id=client_id,
                workflow_id=workflow_id,
                period_type=period_type,
                period_start=start_date,
                period_end=end_date,
                total_executions=total_executions,
                successful_executions=successful_executions,
                failed_executions=failed_executions,
                canceled_executions=canceled_executions,
                success_rate=success_rate,
                avg_execution_time_seconds=avg_execution_time,
                min_execution_time_seconds=min_execution_time,
                max_execution_time_seconds=max_execution_time,
                total_data_size_bytes=total_data_size,
                avg_data_size_bytes=avg_data_size,
                total_workflows=total_workflows,
                active_workflows=active_workflows,
                most_common_error=most_common_error,
                error_count=failed_executions,
                time_saved_hours=time_saved_hours,
                productivity_score=productivity_score,
                computed_at=datetime.now(timezone.utc)
            )
            
            db.add(aggregation)
        
        db.commit()
        return aggregation
    
    def _compute_workflow_period_aggregations_sync(
        self,
        db: Session,
        client_id: int,
        start_date: date,
        end_date: date,
        period_type: AggregationPeriod
    ) -> List[MetricsAggregation]:
        """Synchronous version of _compute_workflow_period_aggregations"""
        # Get all workflows for the client
        workflows_stmt = select(Workflow).where(Workflow.client_id == client_id)
        workflows_result = db.execute(workflows_stmt)
        workflows = workflows_result.scalars().all()
        
        aggregations = []
        for workflow in workflows:
            agg = self._compute_period_aggregation_sync(
                db, client_id, start_date, end_date, period_type, workflow.id
            )
            if agg:
                aggregations.append(agg)
        
        return aggregations
    
    def cleanup_old_data_sync(
        self,
        db: Session,
        raw_execution_retention_days: int = 90,
        aggregation_retention_months: int = 24
    ) -> Dict[str, Any]:
        """Synchronous version of cleanup_old_data"""
        results = {"executions_deleted": 0, "aggregations_deleted": 0, "errors": []}
        
        try:
            # Clean up old raw executions
            execution_cutoff = datetime.now(timezone.utc) - timedelta(days=raw_execution_retention_days)
            
            # Only delete executions that have been aggregated
            # Keep recent executions for real-time queries
            delete_executions_stmt = delete(WorkflowExecution).where(
                and_(
                    WorkflowExecution.created_at < execution_cutoff,
                    WorkflowExecution.started_at < execution_cutoff
                )
            )
            
            executions_result = db.execute(delete_executions_stmt)
            results["executions_deleted"] = executions_result.rowcount
            
            # Clean up old aggregations (keep longer retention)
            aggregation_cutoff = datetime.now(timezone.utc) - timedelta(days=aggregation_retention_months * 30)
            
            delete_aggregations_stmt = delete(MetricsAggregation).where(
                MetricsAggregation.created_at < aggregation_cutoff
            )
            
            aggregations_result = db.execute(delete_aggregations_stmt)
            results["aggregations_deleted"] = aggregations_result.rowcount
            
            # Clean up old trend metrics
            delete_trends_stmt = delete(WorkflowTrendMetrics).where(
                WorkflowTrendMetrics.created_at < aggregation_cutoff
            )
            
            trends_result = db.execute(delete_trends_stmt)
            results["trends_deleted"] = trends_result.rowcount
            
            db.commit()
            
            self.logger.info(
                f"Cleanup completed: deleted {results['executions_deleted']} executions, "
                f"{results['aggregations_deleted']} aggregations, "
                f"{results['trends_deleted']} trend metrics"
            )
            
        except Exception as e:
            db.rollback()
            error_msg = f"Error during cleanup: {e}"
            self.logger.error(error_msg)
            results["errors"].append(error_msg)
        
        return results
    
    def recompute_client_aggregations_sync(
        self,
        db: Session,
        client_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """Synchronous version of recompute_client_aggregations"""
        results = {"recomputed_aggregations": 0, "errors": []}
        
        try:
            # Delete existing aggregations in the date range
            delete_stmt = delete(MetricsAggregation).where(
                and_(
                    MetricsAggregation.client_id == client_id,
                    MetricsAggregation.period_start >= start_date,
                    MetricsAggregation.period_end <= end_date
                )
            )
            db.execute(delete_stmt)
            
            # Recompute daily aggregations for each date in range
            current_date = start_date
            while current_date <= end_date:
                # Client-wide aggregation
                client_agg = self._compute_period_aggregation_sync(
                    db, client_id, current_date, current_date, AggregationPeriod.DAILY
                )
                if client_agg:
                    results["recomputed_aggregations"] += 1
                
                # Workflow-specific aggregations
                workflow_aggs = self._compute_workflow_period_aggregations_sync(
                    db, client_id, current_date, current_date, AggregationPeriod.DAILY
                )
                results["recomputed_aggregations"] += len(workflow_aggs)
                
                current_date += timedelta(days=1)
            
            db.commit()
            
        except Exception as e:
            db.rollback()
            error_msg = f"Error recomputing aggregations for client {client_id}: {e}"
            self.logger.error(error_msg)
            results["errors"].append(error_msg)
        
        return results


# Global service instance
metrics_aggregator = MetricsAggregator()