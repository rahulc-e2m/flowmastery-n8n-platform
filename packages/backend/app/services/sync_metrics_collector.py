"""Synchronous metrics collector for background tasks (Celery)"""

import logging
import httpx
from datetime import datetime, timezone, date
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func, delete

from app.models import (
    Client,
    Workflow,
    WorkflowExecution,
    ExecutionStatus,
    ExecutionMode,
    SyncState
)
from app.services.client_service import ClientService

logger = logging.getLogger(__name__)


class SyncMetricsCollector:
    """Synchronous metrics collector for use in Celery tasks"""
    
    def __init__(self):
        self.max_retries = 3
        self.timeout = 30.0
        
    def sync_client_data(self, db: Session, client_id: int) -> Dict[str, Any]:
        """Sync all data for a specific client"""
        try:
            # Get client configuration
            client = db.query(Client).filter(Client.id == client_id).first()
            if not client:
                logger.error(f"Client {client_id} not found")
                return {'error': f'Client {client_id} not found'}
            
            if not client.n8n_api_url:
                logger.warning(f"Client {client.name} has no n8n API URL configured")
                return {'error': 'n8n API not configured'}
            
            # Get API key from encrypted storage
            api_key = ClientService.get_n8n_api_key_sync(db, client_id)
            if not api_key:
                logger.warning(f"Client {client.name} has no n8n API key configured")
                return {'error': 'n8n API key not configured'}
            
            # Initialize HTTP client with credentials
            headers = {
                'X-N8N-API-KEY': api_key,
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            results = {
                'client_id': client_id,
                'client_name': client.name,
                'sync_started': datetime.now(timezone.utc).isoformat()
            }
            
            with httpx.Client(timeout=self.timeout, headers=headers) as http_client:
                # Sync workflows
                workflow_result = self._sync_workflows(db, client, http_client)
                results['workflows'] = workflow_result
                
                # Sync executions
                execution_result = self._sync_executions(db, client, http_client)
                results['executions'] = execution_result
                
                # Update overall metrics
                metrics_result = self._update_client_metrics(db, client)
                results['metrics'] = metrics_result
                
                # Create snapshot
                snapshot_result = self._create_metric_snapshot(db, client)
                results['snapshot'] = snapshot_result
                
            results['sync_completed'] = datetime.now(timezone.utc).isoformat()
            results['status'] = 'success'
            
            # Commit all changes
            db.commit()
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to sync client {client_id}: {str(e)}")
            db.rollback()
            return {
                'error': str(e),
                'client_id': client_id,
                'status': 'failed'
            }
    
    def _sync_workflows(self, db: Session, client: Client, http_client: httpx.Client) -> Dict[str, Any]:
        """Sync workflows for a client"""
        try:
            workflows = []
            cursor = None
            page = 0
            
            # Paginate through all workflows
            while True:
                url = f"{client.n8n_api_url}/workflows"
                params = {'limit': 100}
                if cursor:
                    params['cursor'] = cursor
                    
                response = http_client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                if isinstance(data, dict) and 'data' in data:
                    batch_workflows = data['data']
                    # Include ALL workflows (archived and non-archived) for proper sync
                    workflows.extend(batch_workflows)
                    cursor = data.get('nextCursor')
                    if not cursor:
                        break
                else:
                    # Handle non-paginated response
                    batch_data = data if isinstance(data, list) else [data]
                    # Include ALL workflows (archived and non-archived) for proper sync
                    workflows.extend(batch_data)
                    break
                    
                page += 1
                if page > 10:  # Safety limit
                    break
            
            # Count active vs archived workflows for logging
            active_count = sum(1 for wf in workflows if not wf.get('isArchived', False))
            archived_count = len(workflows) - active_count
            logger.info(f"Synced {len(workflows)} workflows for client {client.id} ({active_count} active, {archived_count} archived)")
            
            # Store workflows in database
            workflow_ids = []
            stored_workflows = 0
            updated_workflows = 0
            
            for wf_data in workflows:
                workflow = db.query(Workflow).filter(
                    Workflow.client_id == client.id,
                    Workflow.n8n_workflow_id == wf_data.get('id')
                ).first()
                
                if not workflow:
                    workflow = Workflow(
                        client_id=client.id,
                        n8n_workflow_id=wf_data.get('id'),
                        name=wf_data.get('name', 'Unnamed'),
                        active=wf_data.get('active', False),
                        archived=wf_data.get('isArchived', False),
                        nodes=len(wf_data.get('nodes', [])),
                        n8n_created_at=datetime.fromisoformat(wf_data['createdAt'].replace('Z', '+00:00')) 
                            if wf_data.get('createdAt') else None,
                        n8n_updated_at=datetime.fromisoformat(wf_data['updatedAt'].replace('Z', '+00:00'))
                            if wf_data.get('updatedAt') else None,
                        last_synced_at=datetime.now(timezone.utc),
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc)
                    )
                    db.add(workflow)
                    stored_workflows += 1
                else:
                    workflow.name = wf_data.get('name', 'Unnamed')
                    workflow.active = wf_data.get('active', False)
                    workflow.archived = wf_data.get('isArchived', False)
                    workflow.nodes = len(wf_data.get('nodes', []))
                    workflow.n8n_updated_at = datetime.fromisoformat(wf_data['updatedAt'].replace('Z', '+00:00')) if wf_data.get('updatedAt') else None
                    workflow.last_synced_at = datetime.now(timezone.utc)
                    workflow.updated_at = datetime.now(timezone.utc)
                    updated_workflows += 1
                
                workflow_ids.append(wf_data.get('id'))
            
            db.flush()  # Ensure workflows are saved before continuing
            
            # Update workflow sync state
            from app.models import SyncState
            sync_state = db.query(SyncState).filter(SyncState.client_id == client.id).first()
            if not sync_state:
                sync_state = SyncState(client_id=client.id)
                db.add(sync_state)
                db.flush()
            
            sync_state.update_workflow_sync(len(workflows))
            db.flush()
            
            logger.info(f"Workflow sync: {stored_workflows} new, {updated_workflows} updated, {len(workflows)} total")
            
            return {
                'total': len(workflows),
                'workflow_ids': workflow_ids[:10]  # Return sample IDs
            }
            
        except Exception as e:
            logger.error(f"Failed to sync workflows: {str(e)}")
            return {'error': str(e), 'total': 0}
    
    def _sync_executions(self, db: Session, client: Client, http_client: httpx.Client) -> Dict[str, Any]:
        """Sync executions for a client with incremental sync support"""
        try:
            # Get or create sync state for this client
            sync_state = db.query(SyncState).filter(SyncState.client_id == client.id).first()
            if not sync_state:
                sync_state = SyncState(client_id=client.id)
                db.add(sync_state)
                db.flush()
            
            executions = []
            cursor = None
            page = 0
            max_pages = 10  # Limit to prevent excessive API calls
            
            # Determine date range for incremental sync
            from datetime import timedelta
            now = datetime.now(timezone.utc)
            
            # If we have a previous sync, only get executions since then
            # Otherwise, get last 30 days of data
            if sync_state.last_execution_sync:
                # Add a small overlap (1 hour) to catch any updates
                start_date = sync_state.last_execution_sync - timedelta(hours=1)
                logger.info(f"Incremental sync: fetching executions since {start_date}")
            else:
                # First sync - get last 30 days
                start_date = now - timedelta(days=30)
                logger.info(f"Initial sync: fetching executions from last 30 days")
            
            # Fetch executions with pagination
            while page < max_pages:
                url = f"{client.n8n_api_url}/executions"
                params = {'limit': 100}
                if cursor:
                    params['cursor'] = cursor
                    
                response = http_client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                if isinstance(data, dict) and 'data' in data:
                    executions.extend(data['data'])
                    cursor = data.get('nextCursor')
                    if not cursor:
                        break
                else:
                    executions.extend(data if isinstance(data, list) else [data])
                    break
                    
                page += 1
            
            # Filter production executions using sophisticated filtering
            from app.services.production_filter import production_filter
            from app.models import Workflow
            
            # Get workflows for context from database
            workflows_dict = {}
            db_workflows = db.query(Workflow).filter(Workflow.client_id == client.id).all()
            for workflow in db_workflows:
                workflows_dict[str(workflow.n8n_workflow_id)] = {
                    'id': workflow.n8n_workflow_id,
                    'name': workflow.name,
                    'active': workflow.active,
                    'tags': []  # Could be enhanced to include actual tags if available
                }
            
            # Apply production filtering with workflow context
            custom_filters = production_filter.get_production_filter_config(client.id)
            production_executions = production_filter.validate_execution_batch(
                executions, workflows_dict, custom_filters
            )
            
            logger.info(f"Filtered {len(executions)} executions to {len(production_executions)} production executions ({len(production_executions)/max(1, len(executions))*100:.1f}% production rate)")
            
            # Process and store execution data
            stored_executions = 0
            status_counts = {}
            
            for exec_data in production_executions:
                n8n_execution_id = exec_data.get('id')
                workflow_id = exec_data.get('workflowId')
                
                if not n8n_execution_id or not workflow_id:
                    continue
                
                # Find the workflow in our database
                workflow = db.query(Workflow).filter(
                    Workflow.client_id == client.id,
                    Workflow.n8n_workflow_id == workflow_id
                ).first()
                
                if not workflow:
                    continue
                
                # Map status first
                status_mapping = {
                    'success': ExecutionStatus.SUCCESS,
                    'finished': ExecutionStatus.SUCCESS,
                    'error': ExecutionStatus.ERROR,
                    'waiting': ExecutionStatus.WAITING,
                    'running': ExecutionStatus.RUNNING,
                    'canceled': ExecutionStatus.CANCELED,
                    'crashed': ExecutionStatus.CRASHED,
                    'new': ExecutionStatus.NEW,
                    'unknown': ExecutionStatus.NEW
                }
                
                # Check if n8n provides a status field directly
                n8n_status = exec_data.get('status')
                if n8n_status:
                    raw_status = n8n_status.lower()
                else:
                    # Infer from execution data when no status field
                    finished = exec_data.get('finished')
                    started_at = exec_data.get('startedAt')
                    stopped_at = exec_data.get('stoppedAt')
                    has_error = 'error' in exec_data
                    
                    if finished and started_at and stopped_at:
                        # Execution completed - check if it has an error
                        if has_error:
                            raw_status = 'error'
                        else:
                            raw_status = 'success'
                    elif finished == False and started_at and stopped_at:
                        # Started and stopped but not finished - likely failed
                        # This is the key case for executions like 6481
                        raw_status = 'error'
                    elif finished == False and started_at and not stopped_at:
                        # Currently running
                        raw_status = 'running'
                    elif finished == False and not started_at and stopped_at:
                        # Failed to start or was cancelled
                        raw_status = 'error'
                    elif finished == False and not started_at and not stopped_at:
                        # Waiting to start
                        raw_status = 'waiting'
                    else:
                        # Unknown state
                        raw_status = 'unknown'
                
                status = status_mapping.get(raw_status, ExecutionStatus.NEW)
                
                # Track status counts for debugging
                status_counts[raw_status] = status_counts.get(raw_status, 0) + 1
                
                # Log unknown statuses for debugging
                if raw_status and raw_status not in status_mapping:
                    logger.warning(f"Unknown execution status from n8n: '{raw_status}' for execution {n8n_execution_id}")
                
                # Map mode
                mode_mapping = {
                    'manual': ExecutionMode.MANUAL,
                    'trigger': ExecutionMode.TRIGGER,
                    'retry': ExecutionMode.RETRY,
                    'webhook': ExecutionMode.WEBHOOK,
                    'error_trigger': ExecutionMode.ERROR_TRIGGER
                }
                
                mode = mode_mapping.get(exec_data.get('mode', '').lower(), ExecutionMode.TRIGGER)
                
                # Parse timestamps
                started_at = None
                finished_at = None
                stopped_at = None
                execution_time_ms = None
                
                if exec_data.get('startedAt'):
                    try:
                        started_at = datetime.fromisoformat(exec_data['startedAt'].replace('Z', '+00:00'))
                    except:
                        pass
                
                if exec_data.get('stoppedAt'):
                    try:
                        stopped_at = datetime.fromisoformat(exec_data['stoppedAt'].replace('Z', '+00:00'))
                        finished_at = stopped_at  # Use stopped_at as finished_at
                    except:
                        pass
                
                # Calculate execution time
                if started_at and finished_at:
                    execution_time_ms = int((finished_at - started_at).total_seconds() * 1000)
                
                # Check if execution already exists
                existing_execution = db.query(WorkflowExecution).filter(
                    WorkflowExecution.n8n_execution_id == n8n_execution_id
                ).first()
                
                if existing_execution:
                    # Update existing execution with latest data from n8n
                    # Always update status as it might have changed
                    existing_execution.status = status
                    existing_execution.mode = mode
                    
                    # Update timestamps if they are available
                    if started_at:
                        existing_execution.started_at = started_at
                    if finished_at:
                        existing_execution.finished_at = finished_at
                    if stopped_at:
                        existing_execution.stopped_at = stopped_at
                    
                    # Update execution time
                    if execution_time_ms is not None:
                        existing_execution.execution_time_ms = execution_time_ms
                    
                    # Update error message if execution failed
                    if status == ExecutionStatus.ERROR and exec_data.get('error'):
                        error_msg = str(exec_data.get('error', {}).get('message', ''))[:500]
                        if error_msg:
                            existing_execution.error_message = error_msg
                    
                    # Update data size if available
                    if exec_data.get('data'):
                        import json
                        try:
                            data_size = len(json.dumps(exec_data['data']))
                            existing_execution.data_size_bytes = data_size
                        except:
                            pass
                    
                    # Always update sync timestamps
                    existing_execution.last_synced_at = datetime.now(timezone.utc)
                    existing_execution.updated_at = datetime.now(timezone.utc)
                    
                    stored_executions += 1
                    continue
                
                # Create execution record
                execution = WorkflowExecution(
                    n8n_execution_id=n8n_execution_id,
                    workflow_id=workflow.id,
                    client_id=client.id,
                    status=status,
                    mode=mode,
                    started_at=started_at,
                    finished_at=finished_at,
                    stopped_at=stopped_at,
                    execution_time_ms=execution_time_ms,
                    is_production=True,  # We already filtered for production
                    last_synced_at=datetime.now(timezone.utc),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                
                db.add(execution)
                stored_executions += 1
            
            db.flush()
            
            # Update sync state with the latest sync information
            # Always update sync state, even if no new executions (to track sync attempts)
            sync_state.update_execution_sync(
                execution_count=stored_executions,  # Only count actually stored executions
                newest_date=now
            )
            db.flush()
            
            logger.info(f"Updated sync state: {stored_executions} new executions, total synced now: {sync_state.total_executions_synced}")
            
            logger.info(f"Status distribution: {status_counts}")
            logger.info(f"Sync state updated: {stored_executions} executions synced")
            
            return {
                'total': len(executions),
                'production': len(production_executions),
                'stored_executions': stored_executions,
                'status_counts': status_counts,
                'incremental_sync': bool(sync_state.last_execution_sync)
            }
            
        except Exception as e:
            logger.error(f"Failed to sync executions: {str(e)}")
            return {'error': str(e), 'total': 0}
    
    def _update_client_metrics(self, db: Session, client: Client) -> Dict[str, Any]:
        """Update overall client metrics"""
        try:
            # Get workflow counts
            total_workflows = db.query(func.count(Workflow.id)).filter(
                Workflow.client_id == client.id
            ).scalar() or 0
            
            active_workflows = db.query(func.count(Workflow.id)).filter(
                Workflow.client_id == client.id,
                Workflow.active == True
            ).scalar() or 0
            
            # Get execution metrics - using separate queries for clarity
            total_executions = db.query(func.count(WorkflowExecution.id)).filter(
                WorkflowExecution.client_id == client.id,
                WorkflowExecution.is_production == True
            ).scalar() or 0
            
            successful_executions = db.query(func.count(WorkflowExecution.id)).filter(
                WorkflowExecution.client_id == client.id,
                WorkflowExecution.is_production == True,
                WorkflowExecution.status == ExecutionStatus.SUCCESS
            ).scalar() or 0
            
            failed_executions = db.query(func.count(WorkflowExecution.id)).filter(
                WorkflowExecution.client_id == client.id,
                WorkflowExecution.is_production == True,
                WorkflowExecution.status == ExecutionStatus.ERROR
            ).scalar() or 0
            
            avg_execution_time_ms = db.query(func.avg(WorkflowExecution.execution_time_ms)).filter(
                WorkflowExecution.client_id == client.id,
                WorkflowExecution.is_production == True,
                WorkflowExecution.execution_time_ms.isnot(None)
            ).scalar() or 0
            
            avg_execution_time = float(avg_execution_time_ms) / 1000.0 if avg_execution_time_ms else 0
            
            success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0
            
            return {
                'total_workflows': total_workflows,
                'active_workflows': active_workflows,
                'total_executions': total_executions,
                'successful_executions': successful_executions,
                'failed_executions': failed_executions,
                'success_rate': round(success_rate, 1),
                'avg_execution_time': round(avg_execution_time, 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to update client metrics: {str(e)}")
            return {'error': str(e)}
    
    def _create_metric_snapshot(self, db: Session, client: Client) -> Dict[str, Any]:
        """Create a metric snapshot for historical tracking"""
        try:
            # For now, just return success since we don't have a snapshot model
            # This could be implemented later with a proper MetricSnapshot model
            return {
                'snapshot_created': True,
                'snapshot_date': datetime.now(timezone.utc).date().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to create metric snapshot: {str(e)}")
            return {'error': str(e)}
    
    def sync_all_clients(self, db: Session) -> Dict[str, Any]:
        """Sync metrics for all configured clients"""
        results = {
            'synced_clients': 0,
            'errors': [],
            'total_workflows': 0,
            'total_executions': 0
        }
        
        try:
            # Get all clients with n8n configuration
            clients = db.query(Client).filter(
                Client.n8n_api_url.isnot(None)
            ).all()
            
            for client in clients:
                try:
                    client_result = self.sync_client_data(db, client.id)
                    
                    if client_result.get('status') == 'success':
                        results['synced_clients'] += 1
                        results['total_workflows'] += client_result.get('workflows', {}).get('total', 0)
                        results['total_executions'] += client_result.get('executions', {}).get('total', 0)
                    else:
                        results['errors'].append(f"Client {client.name}: {client_result.get('error')}")
                        
                except Exception as e:
                    error_msg = f"Failed to sync client {client.name}: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to sync all clients: {str(e)}")
            return {
                'synced_clients': 0,
                'errors': [str(e)],
                'total_workflows': 0,
                'total_executions': 0
            }


# Global instance
sync_metrics_collector = SyncMetricsCollector()
