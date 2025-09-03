"""Workflow endpoints for listing and updating per-workflow settings with service layer protection"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.core.dependencies import (
    get_current_admin_user,
    get_current_client_user,
    get_current_user,
)
from app.services.workflow_service import workflow_service
from app.core.decorators import validate_input, sanitize_response
from app.core.response_formatter import format_response
from app.schemas.responses import WorkflowListResponse, WorkflowUpdatedResponse

router = APIRouter()
logger = logging.getLogger(__name__)





@router.get("")
@format_response(
    message="Workflows retrieved successfully"
)
async def list_workflows(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user),
    client_id: Optional[str] = Query(None, description="Filter by client id"),
    active: Optional[bool] = Query(None, description="Filter by active status"),
):
    """List workflows (admin) with service layer protection. Optionally filter by client."""
    result = await workflow_service.get_all_workflows(db, client_id, active)
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error
        )
    
    return result.data


@router.get("/my")
@format_response(
    message="Your workflows retrieved successfully"
)
async def list_my_workflows(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_client_user),
    active: Optional[bool] = Query(None, description="Filter by active status"),
):
    """List workflows for the current client user."""
    result = await workflow_service.get_user_workflows(db, current_user, active)
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error
        )
    
    return result.data


@router.patch("/{workflow_db_id}", response_model=WorkflowUpdatedResponse)
@validate_input(max_string_length=100)
@sanitize_response()
@format_response(
    message="Workflow time saved updated successfully",
    response_model=WorkflowUpdatedResponse
)
async def update_workflow_time_saved(
    workflow_db_id: int,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update the per-execution minutes saved for a workflow with service layer protection.
    Admins can update any workflow. Clients can only update their own workflows.
    """
    # Input validation
    minutes = payload.get("time_saved_per_execution_minutes")
    if minutes is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Missing time_saved_per_execution_minutes"
        )
    
    result = await workflow_service.update_workflow_time_saved(db, workflow_db_id, minutes, current_user)
    
    if not result.success:
        if "not found" in result.error.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result.error)
        elif "access denied" in result.error.lower() or "not allowed" in result.error.lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=result.error)
        elif "invalid" in result.error.lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.error)
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.error)
    
    return result.data


