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
                from app.core.service_layer import OperationContext, OperationType
                from app.services.system_service import system_service
                
                # Create operation context
                context = OperationContext(
                    operation_type=OperationType.READ,
                    user_id=current_user.id
                )
                
                # Get all clients using service layer
                clients_result = await system_service.get_clients_for_sync(db, context, with_n8n_config_only=False)
                
                if not clients_result.success:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=clients_result.error or "Failed to get clients"
                    )
                
                clients = clients_result.data
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
        from app.core.service_layer import OperationContext, OperationType
        
        # Create operation context
        context = OperationContext(
            operation_type=OperationType.READ,
            user_id=current_user.id
        )
        
        # Use MetricsService to get executions
        result = await metrics_service.get_client_executions(
            db=db,
            client_id=target_client_id,
            limit=limit,
            offset=offset,
            workflow_id=workflow_id,
            status=status,
            context=context
        )
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.error or "Failed to get executions"
            )
        
        return result.data
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
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
        from app.core.service_layer import OperationContext, OperationType
        
        # Create operation context
        context = OperationContext(
            operation_type=OperationType.READ,
            user_id=current_user.id
        )
        
        # Use MetricsService to get execution stats
        result = await metrics_service.get_client_execution_stats(
            db=db,
            client_id=target_client_id,
            context=context
        )
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.error or "Failed to get execution stats"
            )
        
        return result.data
        
    except HTTPException:
        raise
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
        from app.core.service_layer import OperationContext, OperationType
        
        # Get accessible clients based on role
        accessible_clients = await RoleBasedDataFilter.filter_clients_by_role(
            current_user, db
        )
        
        # Create operation context
        context = OperationContext(
            operation_type=OperationType.READ,
            user_id=current_user.id
        )
        
        # Use MetricsService to get data freshness
        result = await metrics_service.get_data_freshness(
            db=db,
            accessible_clients=accessible_clients,
            context=context
        )
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.error or "Failed to get data freshness"
            )
        
        return result.data
        
    except HTTPException:
        raise
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
                
                # Get all clients and warm cache using service layer
                from app.core.service_layer import OperationContext, OperationType
                from app.services.cache_service import cache_service
                
                # Create operation context
                context = OperationContext(
                    operation_type=OperationType.CREATE,
                    user_id=current_user.id
                )
                
                # Use CacheService to warm all caches
                result = await cache_service.warm_cache(db, None, context)
                
                if not result.success:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=result.error or "Failed to warm cache"
                    )
                
                return {
                    "message": "Cache refreshed for all clients",
                    "warmed_clients": result.data.get('warmed_clients', 0),
                    "total_clients": result.data.get('total_clients', 0),
                    "timestamp": result.data.get('timestamp')
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