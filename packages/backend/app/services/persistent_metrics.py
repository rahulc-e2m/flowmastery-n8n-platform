"""Persistent metrics collection service for background data synchronization"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload

from app.models import (
    Client, 
    Workflow, 
    WorkflowExecution, 
    ExecutionStatus, 
    ExecutionMode,
    MetricsAggregation,
    AggregationPeriod
)
from app.database import get_db
from app.services.client_service import ClientService
# Import n8n client directly to avoid loading unnecessary dependencies
from app.services.n8n.client import n8n_client
from app.services.production_filter import production_filter

logger = logging.getLogger(__name__)


class PersistentMetricsCollector:
    """Service for collecting and persisting n8n metrics data"""
    
    def __init__(self):
        self.logger = logger
        
    async def sync_all_clients(self, db: AsyncSession) -> Dict[str, Any]:
        """Sync metrics for all clients with n8n configuration"""
        results = {"synced_clients": 0, "errors": [], "total_workflows": 0, "total_executions": 0}
        
        # Get all clients with n8n configuration
        client_service = ClientService()
        clients = await client_service.get_all_clients(db)
        
        for client in clients:
            try:
                if client.n8n_api_url and client.n8n_api_key_encrypted:
                    client_result = await self.sync_client_data(db, client.id)
                    results["synced_clients"] += 1
                    results["total_workflows"] += client_result.get("workflows_synced", 0)
                    results["total_executions"] += client_result.get("executions_synced", 0)
                else:
                    self.logger.info(f"Skipping client {client.id} - no n8n configuration")
            except Exception as e:
                error_msg = f"Failed to sync client: {str(e)}"
                self.logger.error(error_msg)
                results["errors"].append(error_msg)
        
        return results
    
    async def sync_client_data(self, db: AsyncSession, client_id: str) -> Dict[str, Any]:
        """Sync workflows and executions for a specific client"""
        client_service = ClientService()
        client = await client_service.get_client_by_id(db, client_id)
        if not client:
            raise ValueError(f"Client {client_id} not found")
        
        api_key = await ClientService.get_n8n_api_key(db, client_id)
        if not api_key or not client.n8n_api_url:
            raise ValueError(f"No n8n configuration for client {client_id}")
        
        workflows_synced = await self._sync_workflows(db, client, api_key)
        executions_synced = await self._sync_executions(db, client, api_key)
        
        return {
            "client_id": client_id,
            "workflows_synced": workflows_synced,
            "executions_synced": executions_synced,
            "sync_time": datetime.now(timezone.utc)
        }
    
    async def _sync_workflows(self, db: AsyncSession, client: Client, api_key: str) -> int:
        """Sync workflows from n8n API to database"""
        try:
            # Fetch workflows from n8n
            n8n_workflows = await self._fetch_n8n_workflows(client.n8n_api_url, api_key)
            
            synced_count = 0
            for n8n_workflow in n8n_workflows:
                workflow_id = str(n8n_workflow.get("id", ""))
                
                try:
                    # Try to get existing workflow
                    stmt = select(Workflow).where(
                        and_(
                            Workflow.client_id == client.id,
                            Workflow.n8n_workflow_id == workflow_id
                        )
                    )
                    result = await db.execute(stmt)
                    existing_workflow = result.scalar_one_or_none()
                    
                    if existing_workflow:
                        # Update existing workflow
                        existing_workflow.name = n8n_workflow.get("name", "Unnamed Workflow")
                        existing_workflow.active = n8n_workflow.get("active", False)
                        existing_workflow.archived = n8n_workflow.get("isArchived", False)
                        existing_workflow.last_synced_at = datetime.now(timezone.utc)
                        
                        # Update metadata if available
                        if "updatedAt" in n8n_workflow:
                            try:
                                existing_workflow.n8n_updated_at = datetime.fromisoformat(
                                    n8n_workflow["updatedAt"].replace("Z", "+00:00")
                                )
                            except:
                                pass
                    else:
                        # Create new workflow
                        current_time = datetime.now(timezone.utc)
                        new_workflow = Workflow(
                            n8n_workflow_id=workflow_id,
                            client_id=client.id,
                            name=n8n_workflow.get("name", "Unnamed Workflow"),
                            active=n8n_workflow.get("active", False),
                            archived=n8n_workflow.get("isArchived", False),
                            last_synced_at=current_time,
                            created_at=current_time,  # Explicitly set created_at
                            updated_at=current_time   # Explicitly set updated_at
                        )
                        
                        # Set timestamps if available
                        if "createdAt" in n8n_workflow:
                            try:
                                new_workflow.n8n_created_at = datetime.fromisoformat(
                                    n8n_workflow["createdAt"].replace("Z", "+00:00")
                                )
                            except:
                                pass
                        
                        if "updatedAt" in n8n_workflow:
                            try:
                                new_workflow.n8n_updated_at = datetime.fromisoformat(
                                    n8n_workflow["updatedAt"].replace("Z", "+00:00")
                                )
                            except:
                                pass
                        
                        db.add(new_workflow)
                    
                    synced_count += 1
                    
                except Exception as workflow_error:
                    # Log individual workflow sync errors but continue with others
                    self.logger.warning(f"Failed to sync workflow {workflow_id} for client {client.id}: {workflow_error}")
                    continue
            
            await db.commit()
            self.logger.info(f"Synced {synced_count} workflows for client {client.id}")
            return synced_count
            
        except Exception as e:
            await db.rollback()
            # Store client_id before potential context issues
            client_id_for_log = client.id
            self.logger.error(f"Error syncing workflows for client {client_id_for_log}: {e}")
            raise
    
    async def _sync_executions(self, db: AsyncSession, client: Client, api_key: str, limit: int = 1000) -> int:
        """Sync executions from n8n API to database with production filtering"""
        try:
            # Get workflow mappings and workflow data
            workflow_stmt = select(Workflow).where(Workflow.client_id == client.id)
            workflow_result = await db.execute(workflow_stmt)
            workflows_db = {w.n8n_workflow_id: w for w in workflow_result.scalars().all()}
            workflow_id_map = {w.n8n_workflow_id: w.id for w in workflows_db.values()}
            
            # Fetch workflows from n8n for filtering context
            n8n_workflows = await self._fetch_n8n_workflows(client.n8n_api_url, api_key)
            workflows_n8n = {str(w.get("id", "")): w for w in n8n_workflows}
            
            # Fetch executions from n8n
            n8n_executions = await self._fetch_n8n_executions(client.n8n_api_url, api_key, limit)
            
            # Apply production filtering with workflow context
            custom_filters = production_filter.get_production_filter_config(client.id)
            production_executions = production_filter.validate_execution_batch(
                n8n_executions, workflows_n8n, custom_filters
            )
            
            synced_count = 0
            for n8n_execution in production_executions:
                execution_id = str(n8n_execution.get("id", ""))
                workflow_n8n_id = str(n8n_execution.get("workflowId", ""))
                
                # Skip if workflow not found in our database
                if workflow_n8n_id not in workflow_id_map:
                    continue
                
                # Check if execution exists
                stmt = select(WorkflowExecution).where(
                    WorkflowExecution.n8n_execution_id == execution_id
                )
                result = await db.execute(stmt)
                existing_execution = result.scalar_one_or_none()
                
                if existing_execution:
                    # Update if status changed
                    new_status = self._map_execution_status(n8n_execution)
                    if existing_execution.status != new_status:
                        existing_execution.status = new_status
                        existing_execution.last_synced_at = datetime.now(timezone.utc)
                        
                        # Update timing if finished
                        if "stoppedAt" in n8n_execution and n8n_execution["stoppedAt"]:
                            try:
                                existing_execution.finished_at = datetime.fromisoformat(
                                    n8n_execution["stoppedAt"].replace("Z", "+00:00")
                                )
                            except:
                                pass
                        
                        # Calculate execution time
                        if existing_execution.started_at and existing_execution.finished_at:
                            duration = existing_execution.finished_at - existing_execution.started_at
                            existing_execution.execution_time_ms = int(duration.total_seconds() * 1000)
                else:
                    # Create new execution
                    new_execution = WorkflowExecution(
                        n8n_execution_id=execution_id,
                        workflow_id=workflow_id_map[workflow_n8n_id],
                        client_id=client.id,
                        status=self._map_execution_status(n8n_execution),
                        mode=self._map_execution_mode(n8n_execution.get("mode", "")),
                        is_production=True,  # Already filtered for production
                        last_synced_at=datetime.now(timezone.utc)
                    )
                    
                    # Set timestamps
                    if "startedAt" in n8n_execution and n8n_execution["startedAt"]:
                        try:
                            new_execution.started_at = datetime.fromisoformat(
                                n8n_execution["startedAt"].replace("Z", "+00:00")
                            )
                        except:
                            pass
                    
                    if "stoppedAt" in n8n_execution and n8n_execution["stoppedAt"]:
                        try:
                            new_execution.finished_at = datetime.fromisoformat(
                                n8n_execution["stoppedAt"].replace("Z", "+00:00")
                            )
                        except:
                            pass
                    
                    # Calculate execution time
                    if new_execution.started_at and new_execution.finished_at:
                        duration = new_execution.finished_at - new_execution.started_at
                        new_execution.execution_time_ms = int(duration.total_seconds() * 1000)
                    
                    # Extract additional metadata
                    if "data" in n8n_execution:
                        # Estimate data size (rough approximation)
                        import json
                        try:
                            data_str = json.dumps(n8n_execution["data"])
                            new_execution.data_size_bytes = len(data_str.encode('utf-8'))
                        except:
                            pass
                    
                    # Count nodes if available
                    if "data" in n8n_execution and isinstance(n8n_execution["data"], dict):
                        result_data = n8n_execution["data"]
                        if isinstance(result_data, dict):
                            new_execution.node_count = len(result_data)
                    
                    # Handle error information
                    if "error" in n8n_execution and n8n_execution["error"]:
                        error_info = n8n_execution["error"]
                        if isinstance(error_info, dict):
                            new_execution.error_message = error_info.get("message", "")
                        else:
                            new_execution.error_message = str(error_info)
                    
                    db.add(new_execution)
                
                synced_count += 1
            
            await db.commit()
            
            # Log filtering results
            total_fetched = len(n8n_executions)
            production_count = len(production_executions)
            filter_rate = (production_count / total_fetched * 100) if total_fetched > 0 else 0
            
            self.logger.info(
                f"Synced {synced_count} executions for client {client.id} "
                f"(filtered {total_fetched} -> {production_count} executions, {filter_rate:.1f}% production rate)"
            )
            
            return synced_count
            
        except Exception as e:
            await db.rollback()
            # Store client_id before potential context issues
            client_id_for_log = client.id
            self.logger.error(f"Error syncing executions for client {client_id_for_log}: {e}")
            raise
    
    async def _fetch_n8n_workflows(self, n8n_url: str, api_key: str) -> List[Dict[str, Any]]:
        """Fetch workflows from n8n API, excluding archived workflows"""
        import httpx
        
        all_workflows = []
        cursor = None
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                params = {}
                if cursor:
                    params['cursor'] = cursor
                
                response = await client.get(
                    f"{n8n_url}/workflows",
                    headers={"X-N8N-API-KEY": api_key},
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                workflows = data.get('data', [])
                if not workflows:
                    break
                
                # Include ALL workflows (archived and non-archived) for proper sync
                all_workflows.extend(workflows)
                
                next_cursor = data.get('nextCursor')
                if not next_cursor:
                    break
                cursor = next_cursor
        
        return all_workflows
    
    async def _fetch_n8n_executions(self, n8n_url: str, api_key: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """Fetch executions from n8n API"""
        import httpx
        
        all_executions = []
        cursor = None
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                params = {}
                if cursor:
                    params['cursor'] = cursor
                if limit and len(all_executions) >= limit:
                    break
                    
                batch_limit = min(100, limit - len(all_executions)) if limit else 100
                params['limit'] = batch_limit
                
                response = await client.get(
                    f"{n8n_url}/executions",
                    headers={"X-N8N-API-KEY": api_key},
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                executions = data.get('data', [])
                if not executions:
                    break
                    
                all_executions.extend(executions)
                
                next_cursor = data.get('nextCursor')
                if not next_cursor or (limit and len(all_executions) >= limit):
                    break
                cursor = next_cursor
        
        return all_executions
    
    def _map_execution_status(self, n8n_execution: dict) -> ExecutionStatus:
        """Map n8n execution data to our status enum"""
        # Check if n8n provides a status field directly
        n8n_status = n8n_execution.get('status')
        if n8n_status:
            status_mapping = {
                "success": ExecutionStatus.SUCCESS,
                "error": ExecutionStatus.ERROR,
                "waiting": ExecutionStatus.WAITING,
                "running": ExecutionStatus.RUNNING,
                "canceled": ExecutionStatus.CANCELED,
                "cancelled": ExecutionStatus.CANCELED,
                "crashed": ExecutionStatus.CRASHED,
                "new": ExecutionStatus.NEW
            }
            return status_mapping.get(n8n_status.lower(), ExecutionStatus.NEW)
        
        # Infer from execution data when no status field
        finished = n8n_execution.get('finished')
        started_at = n8n_execution.get('startedAt')
        stopped_at = n8n_execution.get('stoppedAt')
        has_error = 'error' in n8n_execution
        
        if finished and started_at and stopped_at:
            # Execution completed - check if it has an error
            if has_error:
                return ExecutionStatus.ERROR
            else:
                return ExecutionStatus.SUCCESS
        elif finished == False and started_at and stopped_at:
            # Started and stopped but not finished - likely failed
            return ExecutionStatus.ERROR
        elif finished == False and started_at and not stopped_at:
            # Currently running
            return ExecutionStatus.RUNNING
        elif finished == False and not started_at and stopped_at:
            # Failed to start or was cancelled
            return ExecutionStatus.ERROR
        elif finished == False and not started_at and not stopped_at:
            # Waiting to start
            return ExecutionStatus.WAITING
        else:
            # Unknown state
            return ExecutionStatus.NEW
    
    def _map_execution_mode(self, n8n_mode: str) -> Optional[ExecutionMode]:
        """Map n8n execution mode to our enum"""
        mode_mapping = {
            "manual": ExecutionMode.MANUAL,
            "trigger": ExecutionMode.TRIGGER,
            "retry": ExecutionMode.RETRY,
            "webhook": ExecutionMode.WEBHOOK,
            "error_trigger": ExecutionMode.ERROR_TRIGGER
        }
        return mode_mapping.get(n8n_mode.lower())
    
    def _is_production_execution(self, execution: Dict[str, Any]) -> bool:
        """Determine if execution is production using enhanced filtering"""
        # Use the production filter service for sophisticated filtering
        return production_filter.is_production_execution(
            execution,
            workflow=None,  # We could pass workflow data here if needed
            custom_filters={
                "exclude_manual": True,
                "exclude_test_workflows": True
            }
        )


# Global service instance
persistent_metrics_collector = PersistentMetricsCollector()