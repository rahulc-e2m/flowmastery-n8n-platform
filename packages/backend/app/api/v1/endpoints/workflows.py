"""Consolidated workflow endpoints with role-based access control"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.core.dependencies import get_current_user
from app.core.user_roles import UserRole, RolePermissions
from app.core.role_based_filter import RoleBasedDataFilter
from app.services.workflow_service import workflow_service
from app.core.decorators import validate_input, sanitize_response
from app.core.response_formatter import format_response
from app.schemas.responses import WorkflowListResponse, WorkflowUpdatedResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
@format_response(message="Workflows retrieved successfully")
async def get_workflows(
    client_id: Optional[str] = Query(None, description="Specific client ID (admin only)"),
    active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleBasedDataFilter.get_admin_or_client_user())
):
    """Get workflows - replaces / + /my with role-based filtering"""
    
    if RolePermissions.is_admin(current_user.role):
        if client_id:
            # Admin requesting specific client's workflows
            # Verify client exists
            accessible_client_ids = await RoleBasedDataFilter.get_accessible_client_ids(
                current_user, db, client_id
            )
            if client_id not in accessible_client_ids:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Client not found"
                )
            
            result = await workflow_service.get_all_workflows(db, client_id, active)
        else:
            # Admin requesting all workflows
            result = await workflow_service.get_all_workflows(db, None, active)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.error
            )
        
        return result.data
    
    elif RolePermissions.is_client(current_user.role):
        # Client requesting their own workflows
        if client_id and client_id != current_user.client_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this client's workflows"
            )
        
        result = await workflow_service.get_user_workflows(db, current_user, active)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.error
            )
        
        return result.data
    
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid role"
        )


@router.get("/{workflow_id}")
@format_response(message="Workflow details retrieved successfully")
async def get_workflow_details(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleBasedDataFilter.get_admin_or_client_user())
):
    """Get workflow details by ID"""
    
    # Verify workflow access
    if not await RoleBasedDataFilter.verify_resource_access(
        current_user, "workflow", workflow_id, db
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this workflow"
        )
    
    try:
        # Use the existing get_workflow_by_id method
        result = await workflow_service.get_workflow_by_id(db, workflow_id, current_user)
        
        if not result.success:
            if "not found" in result.error.lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=result.error
                )
            elif "access denied" in result.error.lower():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=result.error
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )
        
        return result.data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow {workflow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve workflow details"
        )


@router.patch("/{workflow_id}", response_model=WorkflowUpdatedResponse)
@validate_input(max_string_length=100)
@sanitize_response()
@format_response(
    message="Workflow updated successfully",
    response_model=WorkflowUpdatedResponse
)
async def update_workflow(
    workflow_id: str,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleBasedDataFilter.get_admin_or_client_user())
):
    """Update workflow settings - admins can update any workflow, clients can only update their own"""
    
    # Verify workflow access
    if not await RoleBasedDataFilter.verify_resource_access(
        current_user, "workflow", workflow_id, db
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this workflow"
        )
    
    try:
        # The workflow_id is already a UUID string (the database primary key)
        workflow_db_id = workflow_id
        
        # Input validation for time saved update
        if "time_saved_per_execution_minutes" in payload:
            minutes = payload.get("time_saved_per_execution_minutes")
            
            if minutes is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="Missing time_saved_per_execution_minutes"
                )
            
            result = await workflow_service.update_workflow_time_saved(
                db, workflow_db_id, minutes, current_user
            )
        else:
            # Future: Add support for other workflow updates
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid update fields provided"
            )
        
        if not result.success:
            if "not found" in result.error.lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=result.error
                )
            elif "access denied" in result.error.lower() or "not allowed" in result.error.lower():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=result.error
                )
            elif "invalid" in result.error.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.error
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )
        
        return result.data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating workflow {workflow_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update workflow: {str(e)}"
        )
