"""Enhanced metrics endpoints for persistent multi-tenant dashboard"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
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