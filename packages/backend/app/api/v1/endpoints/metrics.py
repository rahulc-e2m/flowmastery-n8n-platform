"""Metrics endpoints for multi-tenant dashboard"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.core.dependencies import (
    get_current_admin_user, 
    get_current_client_user,
    get_current_user,
    get_client_for_user,
    verify_client_access
)
from app.services.metrics_service import MetricsService
from app.schemas.metrics import (
    ClientMetrics,
    ClientWorkflowMetrics, 
    AdminMetricsResponse
)

router = APIRouter()


@router.get("/all", response_model=AdminMetricsResponse)
async def get_all_clients_metrics(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Get metrics for all clients (admin only)"""
    return await MetricsService.get_all_clients_metrics(db)


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
        return await MetricsService.get_client_metrics(db, client_id)
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
        return await MetricsService.get_client_workflow_metrics(db, client_id)
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
        return await MetricsService.get_client_metrics(db, current_user.client_id)
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
        return await MetricsService.get_client_workflow_metrics(db, current_user.client_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )