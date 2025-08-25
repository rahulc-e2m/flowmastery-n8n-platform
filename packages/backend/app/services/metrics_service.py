"""Metrics service for fetching n8n data"""

from datetime import datetime
from typing import List, Optional, Dict, Any
import httpx
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.client import Client
from app.services.client_service import ClientService
from app.services.cache.redis import redis_client
from app.schemas.metrics import (
    WorkflowMetrics, 
    ClientMetrics, 
    ClientWorkflowMetrics,
    AdminMetricsResponse,
    MetricsError
)

logger = logging.getLogger(__name__)


class MetricsService:
    """Service for fetching and processing metrics from n8n"""
    
    @staticmethod
    async def get_client_metrics(db: AsyncSession, client_id: int, use_cache: bool = True) -> ClientMetrics:
        """Get aggregated metrics for a specific client"""
        # Try cache first
        cache_key = f"client_metrics:{client_id}"
        if use_cache:
            cached_metrics = await redis_client.get(cache_key)
            if cached_metrics:
                logger.info(f"Using cached client metrics for client {client_id}")
                return ClientMetrics(**cached_metrics)
        
        client = await ClientService.get_client_by_id(db, client_id)
        if not client:
            raise ValueError(f"Client {client_id} not found")
        
        # Get n8n API key
        api_key = await ClientService.get_n8n_api_key(db, client_id)
        if not api_key or not client.n8n_api_url:
            empty_metrics = ClientMetrics(
                client_id=client.id,
                client_name=client.name,
                total_workflows=0,
                active_workflows=0,
                total_executions=0,
                successful_executions=0,
                failed_executions=0,
                success_rate=0.0,
                avg_execution_time=None,
                last_activity=None
            )
            return empty_metrics
        
        try:
            # Fetch workflows and executions from n8n (with caching)
            workflows = await MetricsService._fetch_workflows(client.n8n_api_url, api_key, use_cache)
            executions = await MetricsService._fetch_executions(client.n8n_api_url, api_key, use_cache=use_cache)
            
            # Calculate aggregated metrics
            total_workflows = len(workflows)
            active_workflows = len([w for w in workflows if w.get('active', False)])
            
            total_executions = len(executions)
            successful_executions = len([e for e in executions if e.get('finished', False) and not e.get('stoppedAt')])
            failed_executions = total_executions - successful_executions
            success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0.0
            
            # Calculate average execution time
            execution_times = []
            for execution in executions:
                if execution.get('startedAt') and execution.get('stoppedAt'):
                    start = datetime.fromisoformat(execution['startedAt'].replace('Z', '+00:00'))
                    stop = datetime.fromisoformat(execution['stoppedAt'].replace('Z', '+00:00'))
                    execution_times.append((stop - start).total_seconds())
            
            avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else None
            
            # Get last activity
            last_activity = None
            if executions:
                # Filter out executions without startedAt
                valid_executions = [e for e in executions if e.get('startedAt')]
                if valid_executions:
                    latest_execution = max(valid_executions, key=lambda x: x.get('startedAt', ''))
                    if latest_execution.get('startedAt'):
                        last_activity = datetime.fromisoformat(latest_execution['startedAt'].replace('Z', '+00:00'))
            
            metrics = ClientMetrics(
                client_id=client.id,
                client_name=client.name,
                total_workflows=total_workflows,
                active_workflows=active_workflows,
                total_executions=total_executions,
                successful_executions=successful_executions,
                failed_executions=failed_executions,
                success_rate=round(success_rate, 2),
                avg_execution_time=round(avg_execution_time, 2) if avg_execution_time else None,
                last_activity=last_activity
            )
            
            # Cache the computed metrics for 1 minute
            if use_cache:
                await redis_client.set(cache_key, metrics.model_dump(), expire=60)
                logger.info(f"Cached client metrics for client {client_id}")
            
            return metrics
            
        except Exception as e:
            print(f"Error fetching metrics for client {client_id}: {e}")
            return ClientMetrics(
                client_id=client.id,
                client_name=client.name,
                total_workflows=0,
                active_workflows=0,
                total_executions=0,
                successful_executions=0,
                failed_executions=0,
                success_rate=0.0,
                avg_execution_time=None,
                last_activity=None
            )
    
    @staticmethod
    async def get_client_workflow_metrics(db: AsyncSession, client_id: int) -> ClientWorkflowMetrics:
        """Get workflow-level metrics for a specific client"""
        client = await ClientService.get_client_by_id(db, client_id)
        if not client:
            raise ValueError(f"Client {client_id} not found")
        
        # Get client summary metrics
        client_metrics = await MetricsService.get_client_metrics(db, client_id)
        
        # Get n8n API key
        api_key = await ClientService.get_n8n_api_key(db, client_id)
        if not api_key or not client.n8n_api_url:
            return ClientWorkflowMetrics(
                client_id=client.id,
                client_name=client.name,
                workflows=[],
                summary=client_metrics
            )
        
        try:
            # Fetch workflows and executions
            workflows = await MetricsService._fetch_workflows(client.n8n_api_url, api_key)
            executions = await MetricsService._fetch_executions(client.n8n_api_url, api_key)
            
            # Group executions by workflow
            workflow_executions = {}
            for execution in executions:
                workflow_id = execution.get('workflowId', 'unknown')
                if workflow_id not in workflow_executions:
                    workflow_executions[workflow_id] = []
                workflow_executions[workflow_id].append(execution)
            
            # Calculate metrics for each workflow
            workflow_metrics = []
            for workflow in workflows:
                workflow_id = workflow.get('id', 'unknown')
                workflow_name = workflow.get('name', f'Workflow {workflow_id}')
                workflow_execs = workflow_executions.get(workflow_id, [])
                
                total_executions = len(workflow_execs)
                successful_executions = len([e for e in workflow_execs if e.get('finished', False) and not e.get('stoppedAt')])
                failed_executions = total_executions - successful_executions
                success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0.0
                
                # Calculate average execution time for this workflow
                execution_times = []
                for execution in workflow_execs:
                    if execution.get('startedAt') and execution.get('stoppedAt'):
                        start = datetime.fromisoformat(execution['startedAt'].replace('Z', '+00:00'))
                        stop = datetime.fromisoformat(execution['stoppedAt'].replace('Z', '+00:00'))
                        execution_times.append((stop - start).total_seconds())
                
                avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else None
                
                # Get last execution
                last_execution = None
                if workflow_execs:
                    # Filter out executions without startedAt
                    valid_workflow_execs = [e for e in workflow_execs if e.get('startedAt')]
                    if valid_workflow_execs:
                        latest_exec = max(valid_workflow_execs, key=lambda x: x.get('startedAt', ''))
                        if latest_exec.get('startedAt'):
                            last_execution = datetime.fromisoformat(latest_exec['startedAt'].replace('Z', '+00:00'))
                
                # Determine status
                status = 'active' if workflow.get('active', False) else 'inactive'
                if failed_executions > successful_executions and total_executions > 0:
                    status = 'error'
                
                workflow_metrics.append(WorkflowMetrics(
                    workflow_id=str(workflow_id),
                    workflow_name=workflow_name,
                    total_executions=total_executions,
                    successful_executions=successful_executions,
                    failed_executions=failed_executions,
                    success_rate=round(success_rate, 2),
                    avg_execution_time=round(avg_execution_time, 2) if avg_execution_time else None,
                    last_execution=last_execution,
                    status=status
                ))
            
            return ClientWorkflowMetrics(
                client_id=client.id,
                client_name=client.name,
                workflows=workflow_metrics,
                summary=client_metrics
            )
            
        except Exception as e:
            print(f"Error fetching workflow metrics for client {client_id}: {e}")
            return ClientWorkflowMetrics(
                client_id=client.id,
                client_name=client.name,
                workflows=[],
                summary=client_metrics
            )
    
    @staticmethod
    async def get_all_clients_metrics(db: AsyncSession) -> AdminMetricsResponse:
        """Get metrics for all clients (admin view)"""
        clients = await ClientService.get_all_clients(db)
        client_metrics = []
        
        for client in clients:
            try:
                metrics = await MetricsService.get_client_metrics(db, client.id)
                client_metrics.append(metrics)
            except Exception as e:
                print(f"Error fetching metrics for client {client.id}: {e}")
                # Add empty metrics for failed clients
                client_metrics.append(ClientMetrics(
                    client_id=client.id,
                    client_name=client.name,
                    total_workflows=0,
                    active_workflows=0,
                    total_executions=0,
                    successful_executions=0,
                    failed_executions=0,
                    success_rate=0.0,
                    avg_execution_time=None,
                    last_activity=None
                ))
        
        # Calculate overall metrics
        total_clients = len(client_metrics)
        total_workflows = sum(c.total_workflows for c in client_metrics)
        total_executions = sum(c.total_executions for c in client_metrics)
        total_successful = sum(c.successful_executions for c in client_metrics)
        overall_success_rate = (total_successful / total_executions * 100) if total_executions > 0 else 0.0
        
        return AdminMetricsResponse(
            clients=client_metrics,
            total_clients=total_clients,
            total_workflows=total_workflows,
            total_executions=total_executions,
            overall_success_rate=round(overall_success_rate, 2)
        )
    
    @staticmethod
    async def _fetch_workflows(n8n_url: str, api_key: str, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Fetch all workflows from n8n API with caching"""
        cache_key = f"workflows:{hash(n8n_url + api_key)}"
        
        # Try cache first
        if use_cache:
            cached_workflows = await redis_client.get(cache_key)
            if cached_workflows:
                logger.info(f"Using cached workflows ({len(cached_workflows)} workflows)")
                return cached_workflows
        
        logger.info("Fetching workflows from n8n API...")
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
                    
                all_workflows.extend(workflows)
                
                # Check if there's more data (pagination)
                next_cursor = data.get('nextCursor')
                if not next_cursor:
                    break
                cursor = next_cursor
        
        # Cache workflows for 10 minutes (workflows don't change often)
        if use_cache and all_workflows:
            await redis_client.set(cache_key, all_workflows, expire=600)
            logger.info(f"Cached {len(all_workflows)} workflows for 10 minutes")
                
        return all_workflows
    
    @staticmethod
    async def _fetch_executions(n8n_url: str, api_key: str, limit: int = None, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Fetch executions from n8n API with caching"""
        cache_key = f"executions:{hash(n8n_url + api_key)}:{limit or 1000}"
        
        # Try cache first
        if use_cache:
            cached_executions = await redis_client.get(cache_key)
            if cached_executions:
                logger.info(f"Using cached executions ({len(cached_executions)} executions)")
                return cached_executions
        
        logger.info("Fetching executions from n8n API...")
        all_executions = []
        cursor = None
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                params = {}
                if cursor:
                    params['cursor'] = cursor
                if limit and len(all_executions) >= limit:
                    break
                    
                # Fetch in batches of 100 (n8n's max per request)
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
                
                # Check if there's more data (pagination)
                next_cursor = data.get('nextCursor')
                if not next_cursor:
                    break
                cursor = next_cursor
                
                # If no limit specified, fetch reasonable amount (last 1000 executions)
                if not limit and len(all_executions) >= 1000:
                    break
        
        # Cache executions for 2 minutes (executions change frequently)
        if use_cache and all_executions:
            await redis_client.set(cache_key, all_executions, expire=120)
            logger.info(f"Cached {len(all_executions)} executions for 2 minutes")
                
        return all_executions