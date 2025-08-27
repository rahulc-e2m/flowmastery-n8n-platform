"""Workflow endpoints for listing and updating per-workflow settings"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, case
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.core.dependencies import (
    get_current_admin_user,
    get_current_client_user,
    get_current_user,
)
from app.models import Workflow, WorkflowExecution, ExecutionStatus, Client

router = APIRouter()


async def _format_workflow_rows(db: AsyncSession, rows):
    # rows contains: Workflow, totals
    workflows = []
    for row in rows:
        wf: Workflow = row.Workflow
        total = int(row.total_executions or 0)
        successful = int(row.successful_executions or 0)
        failed = int(row.failed_executions or 0)
        success_rate = (successful / total * 100) if total > 0 else 0.0
        avg_time_ms = float(row.avg_execution_time_ms or 0)
        client_name = row.client_name if hasattr(row, "client_name") else None
        last_execution = row.last_execution

        time_saved_hours = 0.0
        if successful > 0:
            minutes = wf.time_saved_per_execution_minutes or 30
            time_saved_hours = round((successful * minutes) / 60, 2)

        workflows.append({
            "id": wf.id,
            "client_id": wf.client_id,
            "client_name": client_name,
            "n8n_workflow_id": wf.n8n_workflow_id,
            "workflow_name": wf.name,
            "active": wf.active,
            "total_executions": total,
            "successful_executions": successful,
            "failed_executions": failed,
            "success_rate": round(success_rate, 2),
            "avg_execution_time_ms": round(avg_time_ms, 0) if avg_time_ms else 0,
            "avg_execution_time_seconds": round(avg_time_ms / 1000, 2) if avg_time_ms else 0,
            "last_execution": last_execution.isoformat() if last_execution else None,
            "time_saved_per_execution_minutes": wf.time_saved_per_execution_minutes,
            "time_saved_hours": time_saved_hours,
        })
    return workflows


@router.get("")
async def list_workflows(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user),
    client_id: Optional[int] = Query(None, description="Filter by client id"),
    active: Optional[bool] = Query(None, description="Filter by active status"),
):
    """List workflows (admin). Optionally filter by client."""
    try:
        # Base query
        query = select(
            Workflow,
            func.count(WorkflowExecution.id).label("total_executions"),
            func.sum(case((WorkflowExecution.status == ExecutionStatus.SUCCESS, 1), else_=0)).label("successful_executions"),
            func.sum(case((WorkflowExecution.status == ExecutionStatus.ERROR, 1), else_=0)).label("failed_executions"),
            func.avg(WorkflowExecution.execution_time_ms).label("avg_execution_time_ms"),
            func.max(WorkflowExecution.started_at).label("last_execution"),
            Client.name.label("client_name"),
        ).select_from(Workflow).join(Client, Client.id == Workflow.client_id).outerjoin(
            WorkflowExecution,
            and_(Workflow.id == WorkflowExecution.workflow_id, WorkflowExecution.is_production == True),
        )

        if client_id is not None:
            query = query.where(Workflow.client_id == client_id)
        
        if active is not None:
            query = query.where(Workflow.active == active)

        query = query.group_by(Workflow.id, Client.name).order_by(desc(func.max(WorkflowExecution.started_at)))

        result = await db.execute(query)
        rows = result.all()

        workflows = await _format_workflow_rows(db, rows)
        return {"workflows": workflows, "total": len(workflows)}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/my")
async def list_my_workflows(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_client_user),
    active: Optional[bool] = Query(None, description="Filter by active status"),
):
    """List workflows for the current client user."""
    if not current_user.client_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No client associated with user")

    try:
        query = select(
            Workflow,
            func.count(WorkflowExecution.id).label("total_executions"),
            func.sum(case((WorkflowExecution.status == ExecutionStatus.SUCCESS, 1), else_=0)).label("successful_executions"),
            func.sum(case((WorkflowExecution.status == ExecutionStatus.ERROR, 1), else_=0)).label("failed_executions"),
            func.avg(WorkflowExecution.execution_time_ms).label("avg_execution_time_ms"),
            func.max(WorkflowExecution.started_at).label("last_execution"),
        ).select_from(Workflow).outerjoin(
            WorkflowExecution,
            and_(Workflow.id == WorkflowExecution.workflow_id, WorkflowExecution.is_production == True),
        ).where(Workflow.client_id == current_user.client_id)

        if active is not None:
            query = query.where(Workflow.active == active)

        query = query.group_by(Workflow.id).order_by(desc(func.max(WorkflowExecution.started_at)))

        result = await db.execute(query)
        rows = result.all()

        workflows = await _format_workflow_rows(db, rows)
        return {"workflows": workflows, "total": len(workflows)}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{workflow_db_id}")
async def update_workflow_time_saved(
    workflow_db_id: int,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update the per-execution minutes saved for a workflow.
    Admins can update any workflow. Clients can only update their own workflows.
    """
    minutes = payload.get("time_saved_per_execution_minutes")
    if minutes is None or not isinstance(minutes, int) or minutes < 0 or minutes > 24 * 60:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid minutes value")

    # Load workflow
    stmt = select(Workflow).where(Workflow.id == workflow_db_id)
    result = await db.execute(stmt)
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    # Authorization: non-admins can only update their own
    if current_user.role != "admin":
        if current_user.client_id != workflow.client_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    workflow.time_saved_per_execution_minutes = minutes
    await db.commit()
    await db.refresh(workflow)

    return {"id": workflow.id, "time_saved_per_execution_minutes": workflow.time_saved_per_execution_minutes}


