"""Enhanced metrics endpoints for persistent multi-tenant dashboard"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, datetime
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.models import AggregationPeriod
from app.core.dependencies import (
    get_current_admin_user, 
    get_current_client_user,
    get_current_user,
)
from app.services.enhanced_metrics_service import enhanced_metrics_service
from app.services.persistent_metrics import persistent_metrics_collector
from app.schemas.metrics import (
    ClientMetrics,
    ClientWorkflowMetrics, 
    AdminMetricsResponse,
    HistoricalMetrics
)

router = APIRouter()


@router.get("/all", response_model=AdminMetricsResponse)
async def get_all_clients_metrics(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Get metrics for all clients (admin only)"""
    return await enhanced_metrics_service.get_admin_metrics(db)


@router.get("/client/{client_id}", response_model=ClientMetrics)
async def get_client_metrics(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get aggregated metrics for a specific client"""
    # Verify client access
    if current_user.role != "admin" and current_user.client_id != client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this client's metrics"
        )
    
    try:
        return await enhanced_metrics_service.get_client_metrics(db, client_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/client/{client_id}/workflows", response_model=ClientWorkflowMetrics)
async def get_client_workflow_metrics(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get workflow-level metrics for a specific client"""
    # Verify client access
    if current_user.role != "admin" and current_user.client_id != client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this client's metrics"
        )
    
    try:
        return await enhanced_metrics_service.get_client_workflow_metrics(db, client_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/client/{client_id}/historical", response_model=HistoricalMetrics)
async def get_client_historical_metrics(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    period_type: AggregationPeriod = Query(AggregationPeriod.DAILY, description="Aggregation period"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    workflow_id: Optional[int] = Query(None, description="Specific workflow ID")
):
    """Get historical metrics for a client"""
    # Verify client access
    if current_user.role != "admin" and current_user.client_id != client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this client's metrics"
        )
    
    try:
        return await enhanced_metrics_service.get_historical_metrics(
            db, client_id, period_type, start_date, end_date, workflow_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/my-metrics", response_model=ClientMetrics)
async def get_my_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_client_user)
):
    """Get metrics for the current client user"""
    if not current_user.client_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No client associated with user"
        )
    
    try:
        return await enhanced_metrics_service.get_client_metrics(db, current_user.client_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/my-workflows", response_model=ClientWorkflowMetrics)
async def get_my_workflow_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_client_user)
):
    """Get workflow metrics for the current client user"""
    if not current_user.client_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No client associated with user"
        )
    
    try:
        return await enhanced_metrics_service.get_client_workflow_metrics(db, current_user.client_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/my-historical", response_model=HistoricalMetrics)
async def get_my_historical_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_client_user),
    period_type: AggregationPeriod = Query(AggregationPeriod.DAILY),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    workflow_id: Optional[int] = Query(None)
):
    """Get historical metrics for current client user"""
    if not current_user.client_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No client associated with user"
        )
    
    try:
        return await enhanced_metrics_service.get_historical_metrics(
            db, current_user.client_id, period_type, start_date, end_date, workflow_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/admin/quick-sync")
async def quick_sync_all_metrics(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Force immediate sync of all client metrics (admin only)"""
    try:
        # Import here to avoid circular imports
        from app.services.persistent_metrics import persistent_metrics_collector
        from app.services.cache.redis import redis_client
        
        # Clear all cache first
        await redis_client.clear_pattern("enhanced_client_metrics:*")
        await redis_client.clear_pattern("client_metrics:*")
        await redis_client.clear_pattern("admin_metrics:*")
        
        # Sync all clients immediately
        results = []
        from sqlalchemy import select
        from app.models import Client
        
        # Get all clients with n8n configuration
        stmt = select(Client).where(
            Client.n8n_api_url.isnot(None)
        )
        result = await db.execute(stmt)
        clients = result.scalars().all()
        
        for client in clients:
            try:
                sync_result = await persistent_metrics_collector.sync_client_data(db, client.id)
                results.append({
                    "client_id": client.id,
                    "client_name": client.name,
                    "status": "success",
                    "result": sync_result
                })
                
                # Warm cache for this client immediately after sync
                try:
                    await enhanced_metrics_service.get_client_metrics(db, client.id, use_cache=False)
                except Exception as cache_error:
                    logger.warning(f"Failed to warm cache for client {client.id}: {cache_error}")
                    
            except Exception as e:
                results.append({
                    "client_id": client.id,
                    "client_name": client.name,
                    "status": "error",
                    "error": str(e)
                })
        
        # Commit all changes
        await db.commit()
        
        # Warm admin metrics cache
        try:
            await enhanced_metrics_service.get_admin_metrics(db)
        except Exception as cache_error:
            logger.warning(f"Failed to warm admin metrics cache: {cache_error}")
        
        successful = [r for r in results if r["status"] == "success"]
        failed = [r for r in results if r["status"] == "error"]
        
        return {
            "message": f"Quick sync completed: {len(successful)} successful, {len(failed)} failed",
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
            "timestamp": datetime.utcnow().isoformat(),
            "cache_warmed": True
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quick sync failed: {str(e)}"
        )


# Admin endpoints for metrics management
@router.post("/admin/sync/{client_id}")
async def force_sync_client(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Force sync metrics for a specific client (admin only)"""
    try:
        result = await persistent_metrics_collector.sync_client_data(db, client_id)
        return {
            "message": f"Successfully synced client {client_id}",
            "result": result
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )


@router.post("/admin/sync-all")
async def force_sync_all_clients(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Force sync metrics for all clients (admin only)"""
    try:
        result = await persistent_metrics_collector.sync_all_clients(db)
        return {
            "message": "Successfully synced all clients",
            "result": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )


@router.get("/client/{client_id}/executions")
async def get_client_executions(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, description="Number of executions to return"),
    offset: int = Query(0, description="Number of executions to skip"),
    workflow_id: Optional[int] = Query(None, description="Filter by workflow ID"),
    status: Optional[str] = Query(None, description="Filter by status (SUCCESS, ERROR, etc.)")
):
    """Get recent executions for a specific client"""
    # Verify client access
    if current_user.role != "admin" and current_user.client_id != client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this client's executions"
        )
    
    try:
        from sqlalchemy import select, desc, and_
        from app.models import WorkflowExecution, Workflow, ExecutionStatus
        
        # Build query
        query = select(
            WorkflowExecution.n8n_execution_id,
            WorkflowExecution.status,
            WorkflowExecution.mode,
            WorkflowExecution.started_at,
            WorkflowExecution.finished_at,
            WorkflowExecution.execution_time_ms,
            WorkflowExecution.is_production,
            Workflow.name.label('workflow_name'),
            Workflow.n8n_workflow_id
        ).join(Workflow).where(WorkflowExecution.client_id == client_id)
        
        # Apply filters
        if workflow_id:
            query = query.where(WorkflowExecution.workflow_id == workflow_id)
        
        if status:
            try:
                status_enum = ExecutionStatus(status.upper())
                query = query.where(WorkflowExecution.status == status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status}"
                )
        
        # Order by most recent first
        query = query.order_by(desc(WorkflowExecution.started_at))
        
        # Apply pagination
        query = query.offset(offset).limit(limit)
        
        result = await db.execute(query)
        executions = result.all()
        
        # Format response
        execution_list = []
        for exec_row in executions:
            execution_list.append({
                "n8n_execution_id": exec_row.n8n_execution_id,
                "status": exec_row.status.value,
                "mode": exec_row.mode.value if exec_row.mode else None,
                "workflow_name": exec_row.workflow_name,
                "workflow_id": exec_row.n8n_workflow_id,
                "started_at": exec_row.started_at.isoformat() if exec_row.started_at else None,
                "finished_at": exec_row.finished_at.isoformat() if exec_row.finished_at else None,
                "execution_time_ms": exec_row.execution_time_ms,
                "execution_time_seconds": round(exec_row.execution_time_ms / 1000, 2) if exec_row.execution_time_ms else None,
                "is_production": exec_row.is_production
            })
        
        return {
            "executions": execution_list,
            "total_count": len(execution_list),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get executions: {str(e)}"
        )


@router.get("/client/{client_id}/execution-stats")
async def get_client_execution_stats(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get execution statistics grouped by workflow for a specific client"""
    # Verify client access
    if current_user.role != "admin" and current_user.client_id != client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this client's execution stats"
        )
    
    try:
        from sqlalchemy import select, func, case, and_
        from app.models import WorkflowExecution, Workflow, ExecutionStatus
        
        # Query execution stats by workflow
        query = select(
            Workflow.name.label('workflow_name'),
            Workflow.n8n_workflow_id,
            Workflow.active,
            func.count(WorkflowExecution.id).label('total_executions'),
            func.sum(case((WorkflowExecution.status == ExecutionStatus.SUCCESS, 1), else_=0)).label('successful_executions'),
            func.sum(case((WorkflowExecution.status == ExecutionStatus.ERROR, 1), else_=0)).label('failed_executions'),
            func.avg(WorkflowExecution.execution_time_ms).label('avg_execution_time_ms'),
            func.max(WorkflowExecution.started_at).label('last_execution')
        ).select_from(
            Workflow
        ).outerjoin(
            WorkflowExecution, 
            and_(
                Workflow.id == WorkflowExecution.workflow_id,
                WorkflowExecution.is_production == True
            )
        ).where(
            Workflow.client_id == client_id
        ).group_by(
            Workflow.id, Workflow.name, Workflow.n8n_workflow_id, Workflow.active
        ).order_by(
            func.count(WorkflowExecution.id).desc()
        )
        
        result = await db.execute(query)
        stats = result.all()
        
        # Format response
        workflow_stats = []
        for stat_row in stats:
            total = stat_row.total_executions or 0
            successful = stat_row.successful_executions or 0
            failed = stat_row.failed_executions or 0
            success_rate = (successful / total * 100) if total > 0 else 0
            avg_time_ms = float(stat_row.avg_execution_time_ms or 0)
            
            workflow_stats.append({
                "workflow_name": stat_row.workflow_name,
                "workflow_id": stat_row.n8n_workflow_id,
                "active": stat_row.active,
                "total_executions": total,
                "successful_executions": successful,
                "failed_executions": failed,
                "success_rate": round(success_rate, 1),
                "avg_execution_time_ms": round(avg_time_ms, 0) if avg_time_ms else 0,
                "avg_execution_time_seconds": round(avg_time_ms / 1000, 2) if avg_time_ms else 0,
                "last_execution": stat_row.last_execution.isoformat() if stat_row.last_execution else None
            })
        
        return {
            "workflow_stats": workflow_stats,
            "total_workflows": len(workflow_stats)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get execution stats: {str(e)}"
        )


@router.get("/my-executions")
async def get_my_executions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_client_user),
    limit: int = Query(50, description="Number of executions to return"),
    offset: int = Query(0, description="Number of executions to skip"),
    workflow_id: Optional[int] = Query(None, description="Filter by workflow ID"),
    status: Optional[str] = Query(None, description="Filter by status")
):
    """Get recent executions for the current client user"""
    if not current_user.client_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No client associated with user"
        )
    
    return await get_client_executions(
        client_id=current_user.client_id,
        db=db,
        current_user=current_user,
        limit=limit,
        offset=offset,
        workflow_id=workflow_id,
        status=status
    )


@router.get("/my-execution-stats")
async def get_my_execution_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_client_user)
):
    """Get execution statistics for the current client user"""
    if not current_user.client_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No client associated with user"
        )
    
    return await get_client_execution_stats(
        client_id=current_user.client_id,
        db=db,
        current_user=current_user
    )


@router.post("/admin/refresh-cache")
async def refresh_metrics_cache(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Refresh metrics cache without syncing from n8n (admin only)"""
    try:
        from app.services.cache.redis import redis_client
        from sqlalchemy import select
        from app.models import Client
        
        # Clear all metrics cache
        await redis_client.clear_pattern("enhanced_client_metrics:*")
        await redis_client.clear_pattern("client_metrics:*")
        await redis_client.clear_pattern("admin_metrics:*")
        
        # Get all clients
        stmt = select(Client)
        result = await db.execute(stmt)
        clients = result.scalars().all()
        
        # Warm cache for all clients
        warmed_clients = []
        for client in clients:
            try:
                await enhanced_metrics_service.get_client_metrics(db, client.id, use_cache=False)
                warmed_clients.append(client.id)
            except Exception as e:
                logger.warning(f"Failed to warm cache for client {client.id}: {e}")
        
        # Warm admin metrics cache
        await enhanced_metrics_service.get_admin_metrics(db)
        
        return {
            "message": "Cache refreshed successfully",
            "warmed_clients": len(warmed_clients),
            "total_clients": len(clients),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cache refresh failed: {str(e)}"
        )


@router.get("/admin/data-freshness")
async def get_data_freshness(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Get data freshness information for all clients (admin only)"""
    try:
        from sqlalchemy import select, func
        from app.models import Client, WorkflowExecution, MetricsAggregation
        from app.services.cache.redis import redis_client
        
        # Get all clients
        clients_stmt = select(Client)
        clients_result = await db.execute(clients_stmt)
        clients = clients_result.scalars().all()
        
        freshness_data = []
        
        for client in clients:
            # Get last sync time from executions
            last_sync_stmt = select(func.max(WorkflowExecution.last_synced_at)).where(
                WorkflowExecution.client_id == client.id
            )
            last_sync_result = await db.execute(last_sync_stmt)
            last_sync = last_sync_result.scalar_one_or_none()
            
            # Get last aggregation time
            last_agg_stmt = select(func.max(MetricsAggregation.computed_at)).where(
                MetricsAggregation.client_id == client.id
            )
            last_agg_result = await db.execute(last_agg_stmt)
            last_aggregation = last_agg_result.scalar_one_or_none()
            
            # Check cache status
            cache_key = f"enhanced_client_metrics:{client.id}"
            has_cache = await redis_client.exists(cache_key)
            
            # Calculate freshness scores
            now = datetime.utcnow()
            sync_age_minutes = None
            agg_age_minutes = None
            
            if last_sync:
                if last_sync.tzinfo is None:
                    last_sync = last_sync.replace(tzinfo=timezone.utc)
                sync_age_minutes = (now.replace(tzinfo=timezone.utc) - last_sync).total_seconds() / 60
            
            if last_aggregation:
                if last_aggregation.tzinfo is None:
                    last_aggregation = last_aggregation.replace(tzinfo=timezone.utc)
                agg_age_minutes = (now.replace(tzinfo=timezone.utc) - last_aggregation).total_seconds() / 60
            
            freshness_data.append({
                "client_id": client.id,
                "client_name": client.name,
                "last_sync": last_sync.isoformat() if last_sync else None,
                "last_aggregation": last_aggregation.isoformat() if last_aggregation else None,
                "sync_age_minutes": round(sync_age_minutes, 1) if sync_age_minutes else None,
                "aggregation_age_minutes": round(agg_age_minutes, 1) if agg_age_minutes else None,
                "has_cache": has_cache,
                "sync_status": "fresh" if sync_age_minutes and sync_age_minutes < 15 else "stale" if sync_age_minutes else "never",
                "overall_health": "healthy" if (sync_age_minutes and sync_age_minutes < 15 and has_cache) else "degraded"
            })
        
        return {
            "clients": freshness_data,
            "summary": {
                "total_clients": len(clients),
                "healthy_clients": len([c for c in freshness_data if c["overall_health"] == "healthy"]),
                "degraded_clients": len([c for c in freshness_data if c["overall_health"] == "degraded"]),
                "cached_clients": len([c for c in freshness_data if c["has_cache"]]),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get data freshness: {str(e)}"
        )


@router.get("/admin/scheduler-status")
async def get_scheduler_status(
    admin_user: User = Depends(get_current_admin_user)
):
    """Get Celery scheduler status (admin only)"""
    try:
        from app.core.celery_app import celery_app
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        active_tasks = inspect.active()
        scheduled_tasks = inspect.scheduled()
        
        return {
            "celery_workers": stats or {},
            "active_tasks": active_tasks or {},
            "scheduled_tasks": scheduled_tasks or {},
            "beat_schedule": celery_app.conf.beat_schedule
        }
    except Exception as e:
        return {
            "error": f"Failed to get Celery status: {str(e)}",
            "celery_workers": {},
            "active_tasks": {},
            "scheduled_tasks": {}
        }