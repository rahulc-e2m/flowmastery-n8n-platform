"""Vistara workflows endpoints"""

import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.models.workflow import Workflow
from app.models.vistara_workflow import VistaraWorkflow
from app.models.vistara_category import VistaraCategory
from app.services.vistara_workflow_service import vistara_workflow_service
from app.core.dependencies import get_current_user
from app.core.user_roles import RolePermissions
from app.core.role_based_filter import RoleBasedDataFilter
from app.core.decorators import validate_input, sanitize_response
from app.core.response_formatter import format_response

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
@format_response(message="Vistara workflows retrieved successfully")
async def get_vistara_workflows(
    category_id: Optional[str] = Query(None, description="Filter by category ID"),
    is_featured: Optional[bool] = Query(None, description="Filter by featured status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleBasedDataFilter.get_admin_or_client_user())
):
    """Get all vistara workflows (admin-only)"""
    try:
        # Ensure user is admin
        if current_user.role != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vistara access is restricted to administrators only"
            )
        
        # Use the service to get workflows with fresh metrics
        vistara_workflows = await vistara_workflow_service.get_workflows_with_fresh_metrics(
            db=db,
            category_id=category_id,
            is_featured=is_featured,
            sync_before_return=True  # Always sync for fresh data
        )
        
        workflows_data = []
        for vw in vistara_workflows:
            workflow_data = {
                "id": str(vw.id),
                "original_workflow_id": str(vw.original_workflow_id) if vw.original_workflow_id else None,
                "workflow_name": vw.workflow_name,
                "summary": vw.summary,
                "documentation_link": vw.documentation_link,
                "category": {
                    "id": str(vw.category_ref.id),
                    "name": vw.category_ref.name,
                    "color": vw.category_ref.color
                } if vw.category_ref else None,
                "is_featured": vw.is_featured,
                "display_order": vw.display_order,
                "metrics": {
                    "total_executions": vw.total_executions,
                    "successful_executions": vw.successful_executions,
                    "failed_executions": vw.failed_executions,
                    "success_rate": vw.success_rate,
                    "avg_execution_time_ms": vw.avg_execution_time_ms,
                    "manual_time_minutes": vw.manual_time_minutes,
                    "time_saved_per_execution_minutes": vw.time_saved_per_execution_minutes,
                    "total_time_saved_hours": vw.total_time_saved_hours,
                    "last_execution": vw.last_execution.isoformat() if vw.last_execution else None
                },
                "created_at": vw.created_at.isoformat() if vw.created_at else None,
                "updated_at": vw.updated_at.isoformat() if vw.updated_at else None
            }
            workflows_data.append(workflow_data)
        
        return workflows_data
        
    except Exception as e:
        logger.error(f"Error retrieving vistara workflows: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve vistara workflows"
        )


@router.get("/{vistara_workflow_id}")
@format_response(message="Vistara workflow details retrieved successfully")
async def get_vistara_workflow_details(
    vistara_workflow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleBasedDataFilter.get_admin_or_client_user())
):
    """Get vistara workflow details by ID (admin-only)"""
    try:
        # Ensure user is admin
        if current_user.role != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vistara access is restricted to administrators only"
            )
        
        # Get the vistara workflow with fresh metrics and include client and original workflow relationships
        result = await db.execute(
            select(VistaraWorkflow)
            .options(
                selectinload(VistaraWorkflow.client), 
                selectinload(VistaraWorkflow.category_ref),
                selectinload(VistaraWorkflow.original_workflow)
            )
            .filter(VistaraWorkflow.id == vistara_workflow_id)
        )
        vw = result.scalar_one_or_none()
        
        if not vw:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vistara workflow not found"
            )
        
        if not vw:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vistara workflow not found"
            )
        
        return {
            "id": str(vw.id),
            "original_workflow_id": str(vw.original_workflow_id) if vw.original_workflow_id else None,
            "n8n_workflow_id": vw.original_workflow.n8n_workflow_id if vw.original_workflow else None,
            "workflow_name": vw.workflow_name,
            "summary": vw.summary,
            "documentation_link": vw.documentation_link,
            "category": {
                "id": str(vw.category_ref.id),
                "name": vw.category_ref.name,
                "color": vw.category_ref.color,
                "description": vw.category_ref.description
            } if vw.category_ref else None,
            "client": {
                "id": str(vw.client.id),
                "name": vw.client.name,
                "n8n_api_url": vw.client.n8n_api_url
            } if vw.client else None,
            "is_featured": vw.is_featured,
            "display_order": vw.display_order,
            "metrics": {
                "total_executions": vw.total_executions,
                "successful_executions": vw.successful_executions,
                "failed_executions": vw.failed_executions,
                "success_rate": vw.success_rate,
                "avg_execution_time_ms": vw.avg_execution_time_ms,
                "manual_time_minutes": vw.manual_time_minutes,
                "time_saved_per_execution_minutes": vw.time_saved_per_execution_minutes,
                "total_time_saved_hours": vw.total_time_saved_hours,
                "last_execution": vw.last_execution.isoformat() if vw.last_execution else None
            },
            "created_at": vw.created_at.isoformat() if vw.created_at else None,
            "updated_at": vw.updated_at.isoformat() if vw.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving vistara workflow {vistara_workflow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve vistara workflow details"
        )


@router.post("/")
@validate_input(max_string_length=255)
@sanitize_response()
@format_response(message="Vistara workflow created successfully")
async def create_vistara_workflow(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleBasedDataFilter.get_admin_or_client_user())
):
    """Create a new vistara workflow (admin-only)"""
    try:
        # Ensure user is admin
        if current_user.role != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vistara access is restricted to administrators only"
            )
        
        # Validate required fields
        required_fields = ["workflow_name"]
        for field in required_fields:
            if field not in payload:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # Validate original_workflow_id if provided and get workflow data
        original_workflow = None
        original_workflow_id = payload.get("original_workflow_id")
        if original_workflow_id:
            # Check if the workflow exists (admin-only, so allow any workflow)
            workflow_result = await db.execute(
                select(Workflow)
                .filter(Workflow.id == original_workflow_id)
            )
            
            original_workflow = workflow_result.scalar_one_or_none()
            if not original_workflow:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid original workflow ID"
                )
        
        # Validate category_id if provided
        category_id = payload.get("category_id")
        if category_id:
            # Admin-only, allow any active category
            category_result = await db.execute(
                select(VistaraCategory)
                .filter(VistaraCategory.id == category_id)
                .filter(VistaraCategory.is_active == True)
            )
            
            if not category_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid category ID"
                )
        
        # Admin-only: Use the original workflow's client_id for proper organization
        target_client_id = (
            original_workflow.client_id if original_workflow 
            else None  # Fallback if no original workflow
        )
        
        # Get the next display order for the target client
        result = await db.execute(
            select(func.max(VistaraWorkflow.display_order))
            .filter(VistaraWorkflow.client_id == target_client_id)
        )
        max_order = result.scalar()
        next_order = (max_order or 0) + 1
        
        # Copy metrics from original workflow or use defaults/payload values
        if original_workflow:
            # Copy metrics from the original workflow
            total_executions = getattr(original_workflow, 'total_executions', 0)
            successful_executions = getattr(original_workflow, 'successful_executions', 0)
            failed_executions = getattr(original_workflow, 'failed_executions', 0)
            success_rate = getattr(original_workflow, 'success_rate', 0.0)
            avg_execution_time_ms = getattr(original_workflow, 'avg_execution_time_ms', 0) or 0
            time_saved_per_execution_minutes = getattr(original_workflow, 'time_saved_per_execution_minutes', 30)
            time_saved_hours = getattr(original_workflow, 'time_saved_hours', 0.0) or 0.0
            last_execution = getattr(original_workflow, 'last_execution', None)
        else:
            # Use payload values or defaults
            total_executions = payload.get("total_executions", 0)
            successful_executions = payload.get("successful_executions", 0)
            failed_executions = payload.get("failed_executions", 0)
            success_rate = payload.get("success_rate", 0.0)
            avg_execution_time_ms = payload.get("avg_execution_time_ms", 0)
            time_saved_per_execution_minutes = payload.get("time_saved_per_execution_minutes", 30)
            time_saved_hours = payload.get("total_time_saved_hours", 0.0)
            last_execution = None
        
        vistara_workflow = VistaraWorkflow(
            client_id=target_client_id,
            original_workflow_id=original_workflow_id,
            workflow_name=payload["workflow_name"],
            summary=payload.get("summary"),
            documentation_link=payload.get("documentation_link"),
            category_id=category_id,
            is_featured=payload.get("is_featured", False),
            display_order=payload.get("display_order", next_order),
            is_active=True,
            # Use copied or default metrics
            total_executions=total_executions,
            successful_executions=successful_executions,
            failed_executions=failed_executions,
            success_rate=success_rate,
            avg_execution_time_ms=avg_execution_time_ms,
            manual_time_minutes=60,  # Default manual time estimate
            time_saved_per_execution_minutes=time_saved_per_execution_minutes,
            total_time_saved_hours=time_saved_hours,
            last_execution=last_execution,
            created_by=current_user.id
        )
        
        db.add(vistara_workflow)
        await db.commit()
        await db.refresh(vistara_workflow)
        
        return {
            "id": str(vistara_workflow.id),
            "workflow_name": vistara_workflow.workflow_name,
            "summary": vistara_workflow.summary,
            "documentation_link": vistara_workflow.documentation_link,
            "is_featured": vistara_workflow.is_featured,
            "display_order": vistara_workflow.display_order,
            "created_at": vistara_workflow.created_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating vistara workflow: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create vistara workflow"
        )


@router.put("/{vistara_workflow_id}")
@validate_input(max_string_length=255)
@sanitize_response()
@format_response(message="Vistara workflow updated successfully")
async def update_vistara_workflow(
    vistara_workflow_id: str,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleBasedDataFilter.get_admin_or_client_user())
):
    """Update a vistara workflow (admin-only)"""
    try:
        # Ensure user is admin
        if current_user.role != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vistara access is restricted to administrators only"
            )
        
        # Get the vistara workflow (admin can update any workflow) with client and original workflow relationships
        result = await db.execute(
            select(VistaraWorkflow)
            .options(
                selectinload(VistaraWorkflow.client), 
                selectinload(VistaraWorkflow.category_ref),
                selectinload(VistaraWorkflow.original_workflow)
            )
            .filter(VistaraWorkflow.id == vistara_workflow_id)
        )
        vistara_workflow = result.scalar_one_or_none()
        
        if not vistara_workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vistara workflow not found"
            )
        
        # Validate category_id if provided
        category_id = payload.get("category_id")
        if category_id:
            category_result = await db.execute(
                select(VistaraCategory)
                .filter(VistaraCategory.id == category_id)
                .filter(VistaraCategory.client_id == current_user.client_id)
                .filter(VistaraCategory.is_active == True)
            )
            if not category_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid category ID"
                )
        
        # Update fields and calculate manual adjustments for incremental sync
        updatable_fields = [
            "workflow_name", "summary", "documentation_link", "category_id",
            "is_featured", "display_order", "total_executions", "successful_executions",
            "failed_executions", "success_rate", "avg_execution_time_ms",
            "manual_time_minutes", "time_saved_per_execution_minutes", "total_time_saved_hours"
        ]
        
        for field in updatable_fields:
            if field in payload:
                old_value = getattr(vistara_workflow, field)
                new_value = payload[field]
                setattr(vistara_workflow, field, new_value)
                
                # Calculate manual adjustments for execution stats
                # Manual adjustment = (New manually entered value) - (Current n8n baseline value)
                if field == "total_executions":
                    current_n8n_value = vistara_workflow.baseline_total_executions
                    vistara_workflow.manual_total_executions_adjustment = new_value - current_n8n_value
                elif field == "successful_executions":
                    current_n8n_value = vistara_workflow.baseline_successful_executions
                    vistara_workflow.manual_successful_executions_adjustment = new_value - current_n8n_value
                elif field == "failed_executions":
                    current_n8n_value = vistara_workflow.baseline_failed_executions
                    vistara_workflow.manual_failed_executions_adjustment = new_value - current_n8n_value
        
        # Update the updated_at timestamp
        vistara_workflow.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(vistara_workflow)
        
        # Return complete workflow data including metrics
        return {
            "id": str(vistara_workflow.id),
            "original_workflow_id": str(vistara_workflow.original_workflow_id) if vistara_workflow.original_workflow_id else None,
            "n8n_workflow_id": vistara_workflow.original_workflow.n8n_workflow_id if vistara_workflow.original_workflow else None,
            "workflow_name": vistara_workflow.workflow_name,
            "summary": vistara_workflow.summary,
            "documentation_link": vistara_workflow.documentation_link,
            "category": {
                "id": str(vistara_workflow.category_ref.id),
                "name": vistara_workflow.category_ref.name,
                "color": vistara_workflow.category_ref.color,
                "description": vistara_workflow.category_ref.description
            } if vistara_workflow.category_ref else None,
            "client": {
                "id": str(vistara_workflow.client.id),
                "name": vistara_workflow.client.name,
                "n8n_api_url": vistara_workflow.client.n8n_api_url
            } if vistara_workflow.client else None,
            "is_featured": vistara_workflow.is_featured,
            "display_order": vistara_workflow.display_order,
            "metrics": {
                "total_executions": vistara_workflow.total_executions,
                "successful_executions": vistara_workflow.successful_executions,
                "failed_executions": vistara_workflow.failed_executions,
                "success_rate": vistara_workflow.success_rate,
                "avg_execution_time_ms": vistara_workflow.avg_execution_time_ms,
                "manual_time_minutes": vistara_workflow.manual_time_minutes,
                "time_saved_per_execution_minutes": vistara_workflow.time_saved_per_execution_minutes,
                "total_time_saved_hours": vistara_workflow.total_time_saved_hours,
                "last_execution": vistara_workflow.last_execution.isoformat() if vistara_workflow.last_execution else None
            },
            "created_at": vistara_workflow.created_at.isoformat() if vistara_workflow.created_at else None,
            "updated_at": vistara_workflow.updated_at.isoformat() if vistara_workflow.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating vistara workflow {vistara_workflow_id}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update vistara workflow"
        )


@router.delete("/{vistara_workflow_id}")
@format_response(message="Vistara workflow deleted successfully")
async def delete_vistara_workflow(
    vistara_workflow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleBasedDataFilter.get_admin_or_client_user())
):
    """Delete a vistara workflow (admin-only)"""
    try:
        # Ensure user is admin
        if current_user.role != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vistara access is restricted to administrators only"
            )
        
        # Get the vistara workflow (admin can delete from any client)
        result = await db.execute(
            select(VistaraWorkflow)
            .filter(VistaraWorkflow.id == vistara_workflow_id)
        )
        vistara_workflow = result.scalar_one_or_none()
        
        if not vistara_workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vistara workflow not found"
            )
        
        # Instead of deleting, mark as inactive
        vistara_workflow.is_active = False
        await db.commit()
        
        return {"id": str(vistara_workflow.id)}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting vistara workflow {vistara_workflow_id}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete vistara workflow"
        )


@router.get("/available-workflows/")
@format_response(message="Available workflows retrieved successfully")
async def get_available_workflows(
    search: Optional[str] = Query(None, description="Search workflows by name"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleBasedDataFilter.get_admin_or_client_user())
):
    """Get available original workflows that can be added to vistara (admin-only)"""
    try:
        # Ensure user is admin
        if current_user.role != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vistara access is restricted to administrators only"
            )
        
        client_id = current_user.client_id
        user_role = current_user.role
        logger.info(f"Available workflows request - User ID: {current_user.id}, Client ID: {client_id}, Role: {user_role}")
        
        # Vistara is admin-only - show all workflows from all clients that are not in vistara
        subquery = select(VistaraWorkflow.original_workflow_id).filter(
            and_(
                VistaraWorkflow.is_active == True,
                VistaraWorkflow.original_workflow_id.isnot(None)
            )
        )
        
        query = select(Workflow).filter(
            and_(
                Workflow.active == True,
                ~Workflow.id.in_(subquery)
            )
        ).order_by(Workflow.name)
        
        if search:
            query = query.filter(Workflow.name.ilike(f"%{search}%"))
        
        result = await db.execute(query)
        workflows = result.scalars().all()
        
        logger.info(f"Available workflows query returned {len(workflows)} workflows")
        
        # Debug: Log some details about the query (admin-only, so count all workflows)
        total_workflows_result = await db.execute(select(Workflow))
        total_workflows = len(total_workflows_result.scalars().all())
        
        active_workflows_result = await db.execute(
            select(Workflow).filter(Workflow.active == True)
        )
        active_workflows = len(active_workflows_result.scalars().all())
        
        vistara_workflows_result = await db.execute(select(VistaraWorkflow))
        vistara_workflows = len(vistara_workflows_result.scalars().all())
        
        logger.info(f"Debug - Admin Vistara: Total workflows: {total_workflows}, Active: {active_workflows}, Vistara: {vistara_workflows}")
        
        return [
            {
                "id": str(workflow.id),
                "name": workflow.name,
                "description": getattr(workflow, 'description', None),
                "tags": getattr(workflow, 'tags', []) or []
            }
            for workflow in workflows
        ]
        
    except Exception as e:
        logger.error(f"Error retrieving available workflows: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available workflows"
        )


@router.post("/sync-metrics")
@format_response(message="Vistara workflow metrics synchronization completed")
async def sync_vistara_metrics(
    workflow_id: Optional[str] = Query(None, description="Sync specific workflow by ID, or all if not provided"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleBasedDataFilter.get_admin_or_client_user())
):
    """Manually trigger metrics synchronization for Vistara workflows (admin-only)"""
    try:
        # Ensure user is admin
        if current_user.role != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vistara access is restricted to administrators only"
            )
        
        if workflow_id:
            # Sync specific workflow
            vw = await vistara_workflow_service.get_workflow_with_fresh_metrics(
                db=db,
                workflow_id=workflow_id,
                sync_before_return=True
            )
            
            if not vw:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Vistara workflow not found"
                )
            
            if not vw.original_workflow_id:
                return {
                    "workflow_id": workflow_id,
                    "synced": False,
                    "message": "Workflow has no original workflow linked for sync"
                }
            
            return {
                "workflow_id": workflow_id,
                "workflow_name": vw.workflow_name,
                "synced": True,
                "metrics": {
                    "total_executions": vw.total_executions,
                    "successful_executions": vw.successful_executions,
                    "failed_executions": vw.failed_executions,
                    "success_rate": vw.success_rate,
                    "last_execution": vw.last_execution.isoformat() if vw.last_execution else None
                }
            }
        else:
            # Sync all linked workflows
            sync_results = await vistara_workflow_service.sync_all_linked_workflows(db)
            
            return {
                "sync_type": "bulk",
                "results": sync_results,
                "message": f"Synced {sync_results['synced_successfully']} workflows successfully"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing vistara metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync vistara metrics"
        )
