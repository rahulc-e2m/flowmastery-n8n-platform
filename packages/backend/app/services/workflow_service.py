"""
Workflow Service - Manages workflow operations with service layer protection
"""

import logging
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, case
from sqlalchemy.orm import selectinload

from app.core.service_layer import BaseService, OperationContext, OperationType, OperationResult
from app.models import Workflow, WorkflowExecution, ExecutionStatus, Client
from app.models.user import User
from app.core.service_layer import ValidationError

logger = logging.getLogger(__name__)


class WorkflowService(BaseService[Workflow]):
    """Service for managing workflows with full service layer protection"""
    
    @property
    def service_name(self) -> str:
        return "workflow_service"
    
    async def get_all_workflows(
        self, 
        db: AsyncSession, 
        client_id: Optional[str] = None,
        active: Optional[bool] = None,
        use_cache: bool = True
    ) -> OperationResult[Dict[str, Any]]:
        """Get all workflows with execution statistics"""
        context = OperationContext(
            operation_type=OperationType.READ,
            metadata={"client_id": client_id, "active": active}
        )
        
        async def _get_workflows():
            # Check cache first
            if use_cache:
                cache_key = f"all_workflows:{client_id or 'all'}:{active or 'all'}"
                cached_result = await self._get_from_cache(cache_key)
                if cached_result:
                    return cached_result
            
            async with self._get_db_session() as session:
                # Base query with execution statistics
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

                # Apply filters
                if client_id is not None:
                    query = query.where(Workflow.client_id == client_id)
                
                if active is not None:
                    query = query.where(Workflow.active == active)
                
                # Always exclude archived workflows
                query = query.where(Workflow.archived == False)

                query = query.group_by(Workflow.id, Client.name).order_by(desc(func.max(WorkflowExecution.started_at)))

                result = await session.execute(query)
                rows = result.all()

                workflows = await self._format_workflow_rows(rows)
                result_data = {"workflows": workflows, "total": len(workflows)}
                
                # Cache the result
                if use_cache:
                    await self._set_cache(cache_key, result_data, ttl=180)
                
                return result_data
        
        return await self.execute_operation(_get_workflows, context)
    
    async def get_user_workflows(
        self, 
        db: AsyncSession, 
        user: User,
        active: Optional[bool] = None,
        use_cache: bool = True
    ) -> OperationResult[Dict[str, Any]]:
        """Get workflows for a specific user's client"""
        if not user.client_id:
            return OperationResult(success=False, error="No client associated with user")
        
        context = OperationContext(
            operation_type=OperationType.READ,
            user_id=user.id,
            client_id=user.client_id,
            metadata={"active": active}
        )
        
        async def _get_user_workflows():
            # Check cache first
            if use_cache:
                cache_key = f"user_workflows:{user.client_id}:{active or 'all'}"
                cached_result = await self._get_from_cache(cache_key)
                if cached_result:
                    return cached_result
            
            async with self._get_db_session() as session:
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
                ).where(
                    and_(
                        Workflow.client_id == user.client_id,
                        Workflow.archived == False  # Exclude archived workflows
                    )
                )

                if active is not None:
                    query = query.where(Workflow.active == active)

                query = query.group_by(Workflow.id).order_by(desc(func.max(WorkflowExecution.started_at)))

                result = await session.execute(query)
                rows = result.all()

                workflows = await self._format_workflow_rows(rows)
                result_data = {"workflows": workflows, "total": len(workflows)}
                
                # Cache the result
                if use_cache:
                    await self._set_cache(cache_key, result_data, ttl=180)
                
                return result_data
        
        return await self.execute_operation(_get_user_workflows, context)
    
    async def update_workflow_time_saved(
        self,
        db: AsyncSession,
        workflow_id: str,
        minutes: int,
        user: User
    ) -> OperationResult[Dict[str, Any]]:
        """Update time saved per execution for a workflow"""
        context = OperationContext(
            operation_type=OperationType.UPDATE,
            user_id=user.id,
            client_id=user.client_id,
            metadata={"workflow_id": workflow_id, "minutes": minutes}
        )
        
        # Validate input
        if not isinstance(minutes, int) or minutes < 0 or minutes > 24 * 60:
            return OperationResult(success=False, error="Invalid minutes value")
        
        async def _update_workflow():
            # Use the service layer's own database session management
            async with self._get_db_session() as session:
                # Load workflow
                stmt = select(Workflow).where(Workflow.id == workflow_id)
                result = await session.execute(stmt)
                workflow = result.scalar_one_or_none()
                
                if not workflow:
                    return OperationResult(success=False, error="Workflow not found")

                # Authorization: non-admins can only update their own
                if user.role != "admin" and user.client_id != workflow.client_id:
                    return OperationResult(success=False, error="Access denied")

                # Update workflow
                old_minutes = workflow.time_saved_per_execution_minutes
                workflow.time_saved_per_execution_minutes = minutes
                await session.commit()
                await session.refresh(workflow)

                # Invalidate related caches
                await self._invalidate_cache("all_workflows:*")
                await self._invalidate_cache(f"user_workflows:{user.client_id}:*")
                
                # Invalidate metrics caches since time saved affects calculations
                await self._invalidate_cache("metrics_cache:*")

                logger.info(f"Updated workflow {workflow_id} time saved from {old_minutes} to {minutes} by user {user.id}")
                
                # Return complete workflow data to match WorkflowResponse model
                return {
                    "id": workflow.id,
                    "name": workflow.name,
                    "active": workflow.active,
                    "client_id": workflow.client_id,
                    "time_saved_per_execution_minutes": workflow.time_saved_per_execution_minutes,
                    "created_at": workflow.created_at,
                    "updated_at": workflow.updated_at
                }
        
        return await self.execute_operation(_update_workflow, context)
    
    async def get_workflow_by_id(
        self,
        db: AsyncSession,
        workflow_id: str,
        user: User,
        use_cache: bool = True
    ) -> OperationResult[Optional[Workflow]]:
        """Get a specific workflow by ID (database UUID)"""
        context = OperationContext(
            operation_type=OperationType.READ,
            user_id=user.id,
            client_id=user.client_id,
            metadata={"workflow_id": workflow_id}
        )
        
        async def _get_workflow():
            # Check cache first
            if use_cache:
                cache_key = f"workflow:{workflow_id}"
                cached_result = await self._get_from_cache(cache_key)
                if cached_result:
                    return cached_result
            
            async with self._get_db_session() as session:
                # The workflow_id is a UUID string (database primary key)
                stmt = select(Workflow).where(Workflow.id == workflow_id)
                result = await session.execute(stmt)
                workflow = result.scalar_one_or_none()
                
                if not workflow:
                    return None
                
                # Authorization check
                if user.role != "admin" and user.client_id != workflow.client_id:
                    return None
                
                # Cache the result
                if use_cache:
                    workflow_dict = {
                        "id": workflow.id,
                        "client_id": workflow.client_id,
                        "n8n_workflow_id": workflow.n8n_workflow_id,
                        "name": workflow.name,
                        "active": workflow.active,
                        "time_saved_per_execution_minutes": workflow.time_saved_per_execution_minutes
                    }
                    await self._set_cache(cache_key, workflow_dict, ttl=300)
                
                return workflow
        
        return await self.execute_operation(_get_workflow, context)
    
    async def _format_workflow_rows(self, rows) -> List[Dict[str, Any]]:
        """Format workflow query results"""
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
                minutes = wf.time_saved_per_execution_minutes if wf.time_saved_per_execution_minutes is not None else 30
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


# Global service instance
workflow_service = WorkflowService()