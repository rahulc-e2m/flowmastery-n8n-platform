"""Consolidated metrics endpoints with role-based access control"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, datetime, timezone
from typing import Optional
import logging

logger = logging.getLogger(__name__)

from app.database import get_db
from app.models.user import User
from app.models import AggregationPeriod
from app.core.dependencies import get_current_user
from app.core.user_roles import UserRole, RolePermissions
from app.core.role_based_filter import RoleBasedDataFilter
from app.services.metrics_service import metrics_service
from app.services.persistent_metrics import persistent_metrics_collector
from app.schemas.metrics import (
    ClientMetrics,
    ClientWorkflowMetrics, 
    AdminMetricsResponse,
    HistoricalMetrics
)
from app.core.decorators import validate_input, sanitize_response
from app.core.response_formatter import format_response

router = APIRouter()


@router.get("/overview")
@format_response(message="Metrics overview retrieved successfully")
async def get_metrics_overview(
    client_id: Optional[str] = Query(None, description="Specific client ID (admin only)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleBasedDataFilter.get_admin_or_client_user())
):
    """Get metrics overview - replaces /all + /my-metrics + /client/{id}"""
    
    # Get accessible client IDs based on role
    accessible_client_ids = await RoleBasedDataFilter.get_accessible_client_ids(
        current_user, db, client_id
    )
    
    if RolePermissions.is_admin(current_user.role):
        if client_id:
            # Admin requesting specific client
            return await metrics_service.get_client_metrics(db, client_id)
        else:
            # Admin requesting overview of all clients
            return await metrics_service.get_admin_metrics(db)
    
    elif RolePermissions.is_client(current_user.role):
        # Client requesting their own metrics
        if not current_user.client_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No client associated with user"
            )
        return await metrics_service.get_client_metrics(db, current_user.client_id)
    
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid role"
        )


@router.get("/workflows")
@format_response(message="Workflow metrics retrieved successfully")
async def get_workflow_metrics(
    client_id: Optional[str] = Query(None, description="Specific client ID (admin only)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleBasedDataFilter.get_admin_or_client_user())
):
    """Get workflow metrics - replaces /client/{id}/workflows + /my-workflows"""
    
    if RolePermissions.is_admin(current_user.role):
        if client_id:
            # Admin requesting specific client workflows
            try:
                return await metrics_service.get_client_workflow_metrics(db, client_id)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=str(e)
                )
        else:
            # Admin requesting all workflows across all clients
            try:
                from sqlalchemy import select
                from app.models import Client
                
                # Get all clients
                stmt = select(Client)
                result = await db.execute(stmt)
                clients = result.scalars().all()
                
                all_workflows = []
                for client in clients:
                    try:
                        client_workflows = await metrics_service.get_client_workflow_metrics(db, client.id)
                        
                        # Handle different response formats
                        workflows_list = []
                        if hasattr(client_workflows, 'workflows'):
                            workflows_list = client_workflows.workflows
                        elif isinstance(client_workflows, dict) and 'workflows' in client_workflows:
                            workflows_list = client_workflows['workflows']
                        elif isinstance(client_workflows, dict):
                            # If the entire response is the workflows data
                            workflows_list = [client_workflows]
                        
                        # Add client info to each workflow
                        for workflow in workflows_list:
                            if isinstance(workflow, dict):
                                workflow_dict = workflow.copy()
                            else:
                                # Convert Pydantic model to dict
                                workflow_dict = workflow.dict() if hasattr(workflow, 'dict') else workflow.__dict__.copy()
                            
                            workflow_dict['client_id'] = client.id
                            workflow_dict['client_name'] = client.name
                            all_workflows.append(workflow_dict)
                            
                    except Exception as e:
                        logger.warning(f"Failed to get workflows for client {client.id}: {e}")
                        continue
                
                return {
                    "workflows": all_workflows,
                    "total_workflows": len(all_workflows),
                    "total_clients": len(clients),
                    "aggregated": True
                }
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to get aggregated workflow metrics: {str(e)}"
                )
    
    elif RolePermissions.is_client(current_user.role):
        if client_id and client_id != current_user.client_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this client's workflow metrics"
            )
        
        target_client_id = current_user.client_id
        if not target_client_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No client associated with user"
            )
        
        try:
            return await metrics_service.get_client_workflow_metrics(db, target_client_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
    
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid role"
        )


@router.get("/executions")
@format_response(message="Executions retrieved successfully")
async def get_executions(
    client_id: Optional[str] = Query(None, description="Specific client ID (admin only)"),
    limit: int = Query(50, description="Number of executions to return"),
    offset: int = Query(0, description="Number of executions to skip"),
    workflow_id: Optional[int] = Query(None, description="Filter by workflow ID"),
    status: Optional[str] = Query(None, description="Filter by status (SUCCESS, ERROR, etc.)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleBasedDataFilter.get_admin_or_client_user())
):
    """Get executions - replaces /client/{id}/executions + /my-executions"""
    
    # Determine target client ID
    target_client_id = client_id
    
    if RolePermissions.is_admin(current_user.role):
        if not client_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin must specify client_id for executions"
            )
        target_client_id = client_id
    
    elif RolePermissions.is_client(current_user.role):
        if client_id and client_id != current_user.client_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this client's executions"
            )
        target_client_id = current_user.client_id
    
    if not target_client_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No client associated with user"
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
        ).join(Workflow).where(WorkflowExecution.client_id == target_client_id)
        
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
            "offset": offset,
            "client_id": target_client_id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get executions: {str(e)}"
        )


@router.get("/execution-stats")
@format_response(message="Execution statistics retrieved successfully")
async def get_execution_stats(
    client_id: Optional[str] = Query(None, description="Specific client ID (admin only)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleBasedDataFilter.get_admin_or_client_user())
):
    """Get execution statistics - replaces /client/{id}/execution-stats + /my-execution-stats"""
    
    # Determine target client ID
    target_client_id = client_id
    
    if RolePermissions.is_admin(current_user.role):
        if not client_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin must specify client_id for execution stats"
            )
        target_client_id = client_id
    
    elif RolePermissions.is_client(current_user.role):
        if client_id and client_id != current_user.client_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this client's execution stats"
            )
        target_client_id = current_user.client_id
    
    if not target_client_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No client associated with user"
        )
    
    try:
        from sqlalchemy import select, func, case, and_
        from app.models import WorkflowExecution, Workflow, ExecutionStatus
        
        # Query execution stats by workflow
        query = select(
            Workflow.name.label('workflow_name'),
            Workflow.n8n_workflow_id,
            Workflow.active,
            Workflow.time_saved_per_execution_minutes,
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
            Workflow.client_id == target_client_id
        ).group_by(
            Workflow.id, Workflow.name, Workflow.n8n_workflow_id, Workflow.active, Workflow.time_saved_per_execution_minutes
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
            
            # Calculate time saved
            time_saved_per_execution_minutes = stat_row.time_saved_per_execution_minutes or 0
            total_time_saved_minutes = successful * time_saved_per_execution_minutes
            total_time_saved_hours = round(total_time_saved_minutes / 60, 1) if total_time_saved_minutes > 0 else 0
            
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
                "last_execution": stat_row.last_execution.isoformat() if stat_row.last_execution else None,
                "time_saved_per_execution_minutes": time_saved_per_execution_minutes,
                "time_saved_hours": total_time_saved_hours
            })
        
        return {
            "workflow_stats": workflow_stats,
            "total_workflows": len(workflow_stats),
            "client_id": target_client_id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get execution stats: {str(e)}"
        )


@router.get("/historical")
@format_response(message="Historical metrics retrieved successfully")
async def get_historical_metrics(
    client_id: Optional[str] = Query(None, description="Specific client ID (admin only)"),
    period: AggregationPeriod = Query(AggregationPeriod.DAILY, description="Aggregation period"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    workflow_id: Optional[int] = Query(None, description="Specific workflow ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleBasedDataFilter.get_admin_or_client_user())
):
    """Get historical metrics - replaces /client/{id}/historical + /my-historical"""
    
    # Determine target client ID
    target_client_id = client_id
    
    if RolePermissions.is_admin(current_user.role):
        if not client_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin must specify client_id for historical metrics"
            )
        target_client_id = client_id
    
    elif RolePermissions.is_client(current_user.role):
        if client_id and client_id != current_user.client_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this client's historical metrics"
            )
        target_client_id = current_user.client_id
    
    if not target_client_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No client associated with user"
        )
    
    try:
        return await metrics_service.get_historical_metrics(
            db, target_client_id, period, start_date, end_date, workflow_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/data-freshness")
@format_response(message="Data freshness information retrieved successfully")
async def get_data_freshness(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleBasedDataFilter.get_admin_or_client_user())
):
    """Get data freshness information - admin sees all, client sees own"""
    
    try:
        from sqlalchemy import select, func
        from app.models import Client, WorkflowExecution, MetricsAggregation
        from app.services.cache.redis import redis_client
        
        # Get accessible clients based on role
        accessible_clients = await RoleBasedDataFilter.filter_clients_by_role(
            current_user, db
        )
        
        freshness_data = []
        
        for client in accessible_clients:
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
                "total_clients": len(accessible_clients),
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


@router.post("/refresh-cache")
@sanitize_response()
@format_response(message="Metrics cache refreshed successfully")
async def refresh_cache(
    client_id: Optional[str] = Query(None, description="Specific client ID (admin only)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleBasedDataFilter.get_admin_or_client_user())
):
    """Refresh cache - admin can refresh all or specific client, client can refresh own"""
    
    try:
        from app.services.cache.redis import redis_client
        
        if RolePermissions.is_admin(current_user.role):
            if client_id:
                # Admin refreshing specific client
                await redis_client.clear_pattern(f"enhanced_client_metrics:{client_id}")
                await redis_client.clear_pattern(f"client_metrics:{client_id}")
                await metrics_service.get_client_metrics(db, client_id, use_cache=False)
                
                return {
                    "message": f"Cache refreshed for client {client_id}",
                    "client_id": client_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                # Admin refreshing all
                await redis_client.clear_pattern("enhanced_client_metrics:*")
                await redis_client.clear_pattern("client_metrics:*")
                await redis_client.clear_pattern("admin_metrics:*")
                
                # Get all clients and warm cache
                from sqlalchemy import select
                from app.models import Client
                
                stmt = select(Client)
                result = await db.execute(stmt)
                clients = result.scalars().all()
                
                warmed_clients = []
                for client in clients:
                    try:
                        await metrics_service.get_client_metrics(db, client.id, use_cache=False)
                        warmed_clients.append(client.id)
                    except Exception as e:
                        logger.warning(f"Failed to warm cache for client {client.id}: {e}")
                
                # Warm admin metrics cache
                await metrics_service.get_admin_metrics(db)
                
                return {
                    "message": "Cache refreshed for all clients",
                    "warmed_clients": len(warmed_clients),
                    "total_clients": len(clients),
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        elif RolePermissions.is_client(current_user.role):
            # Client refreshing their own cache
            if not current_user.client_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No client associated with user"
                )
            
            target_client_id = current_user.client_id
            await redis_client.clear_pattern(f"enhanced_client_metrics:{target_client_id}")
            await redis_client.clear_pattern(f"client_metrics:{target_client_id}")
            await metrics_service.get_client_metrics(db, target_client_id, use_cache=False)
            
            return {
                "message": "Cache refreshed for your client",
                "client_id": target_client_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid role"
            )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cache refresh failed: {str(e)}"
        )


@router.post("/trigger-aggregation")
@validate_input(max_string_length=50)
@sanitize_response()
@format_response(message="Aggregation triggered successfully")
async def trigger_aggregation(
    target_date: Optional[str] = Query(None, description="Target date (YYYY-MM-DD), defaults to yesterday"),
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_user(required_roles=[UserRole.ADMIN]))
):
    """Trigger aggregation (admin only)"""
    
    try:
        from app.tasks.aggregation_tasks import compute_daily_aggregations
        from datetime import date, timedelta
        
        # Default to yesterday if no date provided
        if target_date:
            computation_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        else:
            computation_date = date.today() - timedelta(days=1)
        
        # Trigger the aggregation task
        task = compute_daily_aggregations.delay(computation_date.isoformat())
        
        return {
            "message": f"Aggregation triggered for {computation_date.isoformat()}",
            "task_id": task.id,
            "target_date": computation_date.isoformat(),
            "status": "queued"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger aggregation: {str(e)}"
        )