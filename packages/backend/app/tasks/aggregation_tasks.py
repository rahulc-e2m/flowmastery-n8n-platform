"""
Celery tasks for metrics aggregation and data maintenance
"""

from datetime import datetime, timedelta, date
from typing import Dict, Any
import asyncio
import concurrent.futures

from celery import Task

from app.core.celery_app import celery_app
from app.database.connection import get_db_session
from app.services.metrics_aggregator import metrics_aggregator


def run_async_task(coro):
    """Run an async coroutine in a thread-safe manner for Celery"""
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(asyncio.run, coro)
        return future.result()


@celery_app.task(bind=True, name="app.tasks.aggregation_tasks.compute_daily_aggregations")
def compute_daily_aggregations(self, target_date: str = None) -> Dict[str, Any]:
    """
    Compute daily metrics aggregations for all clients
    
    Args:
        target_date: Date string in YYYY-MM-DD format (defaults to yesterday)
    
    Returns:
        Dict with computation results
    """
    try:
        if target_date:
            computation_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        else:
            computation_date = date.today() - timedelta(days=1)
        
        async def _compute():
            async with get_db_session() as db:
                return await metrics_aggregator.compute_daily_aggregations(
                    db, computation_date
                )
        
        result = run_async_task(_compute())
        
        return {
            "status": "success",
            "date": computation_date.isoformat(),
            "processed_clients": result.get("processed_clients", 0),
            "total_aggregations": result.get("total_aggregations", 0),
            "task_id": self.request.id
        }
        
    except Exception as e:
        self.retry(
            countdown=60,  # Retry after 1 minute
            max_retries=3,
            exc=e
        )


@celery_app.task(bind=True, name="app.tasks.aggregation_tasks.compute_weekly_aggregations")
def compute_weekly_aggregations(self, target_week: str = None) -> Dict[str, Any]:
    """
    Compute weekly metrics aggregations for all clients
    
    Args:
        target_week: Week start date string in YYYY-MM-DD format
    
    Returns:
        Dict with computation results
    """
    try:
        if target_week:
            week_start = datetime.strptime(target_week, "%Y-%m-%d").date()
        else:
            # Previous week (Monday to Sunday)
            today = date.today()
            days_since_monday = today.weekday()
            week_start = today - timedelta(days=days_since_monday + 7)
        
        async def _compute():
            async with get_db_session() as db:
                return await metrics_aggregator.compute_weekly_aggregations(
                    db, week_start
                )
        
        result = run_async_task(_compute())
        
        return {
            "status": "success",
            "week_start": week_start.isoformat(),
            "processed_clients": result.get("processed_clients", 0),
            "total_aggregations": result.get("total_aggregations", 0),
            "task_id": self.request.id
        }
        
    except Exception as e:
        self.retry(
            countdown=300,  # Retry after 5 minutes
            max_retries=2,
            exc=e
        )


@celery_app.task(bind=True, name="app.tasks.aggregation_tasks.compute_monthly_aggregations")
def compute_monthly_aggregations(self, target_month: str = None) -> Dict[str, Any]:
    """
    Compute monthly metrics aggregations for all clients
    
    Args:
        target_month: Month string in YYYY-MM format
    
    Returns:
        Dict with computation results
    """
    try:
        if target_month:
            year, month = map(int, target_month.split('-'))
            month_start = date(year, month, 1)
        else:
            # Previous month
            today = date.today()
            if today.month == 1:
                month_start = date(today.year - 1, 12, 1)
            else:
                month_start = date(today.year, today.month - 1, 1)
        
        async def _compute():
            async with get_db_session() as db:
                return await metrics_aggregator.compute_monthly_aggregations(
                    db, month_start
                )
        
        result = run_async_task(_compute())
        
        return {
            "status": "success",
            "month": month_start.strftime("%Y-%m"),
            "processed_clients": result.get("processed_clients", 0),
            "total_aggregations": result.get("total_aggregations", 0),
            "task_id": self.request.id
        }
        
    except Exception as e:
        self.retry(
            countdown=600,  # Retry after 10 minutes
            max_retries=2,
            exc=e
        )


@celery_app.task(bind=True, name="app.tasks.aggregation_tasks.cleanup_old_data")
def cleanup_old_data(self, retention_days: int = 365) -> Dict[str, Any]:
    """
    Clean up old execution data and aggregations
    
    Args:
        retention_days: Number of days to retain data (default: 365)
    
    Returns:
        Dict with cleanup results
    """
    try:
        cutoff_date = date.today() - timedelta(days=retention_days)
        
        async def _cleanup():
            async with get_db_session() as db:
                return await metrics_aggregator.cleanup_old_data(
                    db, cutoff_date
                )
        
        result = run_async_task(_cleanup())
        
        return {
            "status": "success",
            "cutoff_date": cutoff_date.isoformat(),
            "deleted_executions": result.get("deleted_executions", 0),
            "deleted_aggregations": result.get("deleted_aggregations", 0),
            "task_id": self.request.id
        }
        
    except Exception as e:
        self.retry(
            countdown=1800,  # Retry after 30 minutes
            max_retries=1,
            exc=e
        )


@celery_app.task(bind=True, name="app.tasks.aggregation_tasks.recompute_aggregations")
def recompute_aggregations(
    self, 
    client_id: int, 
    start_date: str, 
    end_date: str
) -> Dict[str, Any]:
    """
    Recompute aggregations for a specific client and date range
    
    Args:
        client_id: Client ID
        start_date: Start date string in YYYY-MM-DD format
        end_date: End date string in YYYY-MM-DD format
    
    Returns:
        Dict with recomputation results
    """
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        async def _recompute():
            async with get_db_session() as db:
                return await metrics_aggregator.recompute_client_aggregations(
                    db, client_id, start_dt, end_dt
                )
        
        result = run_async_task(_recompute())
        
        return {
            "status": "success",
            "client_id": client_id,
            "start_date": start_date,
            "end_date": end_date,
            "recomputed_aggregations": result.get("recomputed_aggregations", 0),
            "task_id": self.request.id
        }
        
    except Exception as e:
        self.retry(
            countdown=300,  # Retry after 5 minutes
            max_retries=2,
            exc=e
        )