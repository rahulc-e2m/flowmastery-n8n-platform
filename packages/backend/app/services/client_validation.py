"""Client configuration validation service"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.client import Client
from app.models.workflow import Workflow
from app.models.workflow_execution import WorkflowExecution
from app.models.sync_state import SyncState
from app.services.client_service import ClientService
from app.services.n8n.client import N8nClient

logger = logging.getLogger(__name__)


class ClientConfigurationValidator:
    """Service to validate and fix client configuration issues"""
    
    async def validate_all_clients(self, db: AsyncSession) -> Dict[str, Any]:
        """Validate configuration for all clients"""
        results = {
            "total_clients": 0,
            "valid_clients": 0,
            "invalid_clients": [],
            "configuration_issues": [],
            "recommendations": []
        }
        
        # Get all clients
        stmt = select(Client)
        result = await db.execute(stmt)
        clients = result.scalars().all()
        
        results["total_clients"] = len(clients)
        
        for client in clients:
            validation_result = await self.validate_client_configuration(db, client.id)
            
            if validation_result["is_valid"]:
                results["valid_clients"] += 1
            else:
                results["invalid_clients"].append({
                    "client_id": client.id,
                    "client_name": client.name,
                    "issues": validation_result["issues"]
                })
                results["configuration_issues"].extend(validation_result["issues"])
        
        # Generate recommendations
        results["recommendations"] = self._generate_recommendations(results)
        
        return results
    
    async def validate_client_configuration(self, db: AsyncSession, client_id: str) -> Dict[str, Any]:
        """Validate configuration for a specific client"""
        result = {
            "client_id": client_id,
            "is_valid": True,
            "issues": [],
            "warnings": [],
            "data_status": {}
        }
        
        # Get client
        stmt = select(Client).where(Client.id == client_id)
        client_result = await db.execute(stmt)
        client = client_result.scalar_one_or_none()
        
        if not client:
            result["is_valid"] = False
            result["issues"].append("Client not found")
            return result
        
        # Check n8n API configuration
        if not client.n8n_api_url:
            result["is_valid"] = False
            result["issues"].append("Missing n8n API URL")
        
        if not client.n8n_api_key_encrypted:
            result["is_valid"] = False
            result["issues"].append("Missing n8n API key")
        
        # Test n8n connection if configured
        if client.n8n_api_url and client.n8n_api_key_encrypted:
            try:
                api_key = await ClientService.get_n8n_api_key(db, client_id)
                if api_key:
                    connection_test = await ClientService.test_n8n_connection(
                        client.n8n_api_url, api_key
                    )
                    if not connection_test.get("connection_healthy"):
                        result["warnings"].append(f"n8n connection test failed: {connection_test.get('message')}")
                else:
                    result["issues"].append("Failed to decrypt n8n API key")
            except Exception as e:
                result["warnings"].append(f"n8n connection test error: {str(e)}")
        
        # Check data status
        workflow_count = await db.execute(
            select(Workflow).where(Workflow.client_id == client_id)
        )
        result["data_status"]["workflow_count"] = len(workflow_count.scalars().all())
        
        execution_count = await db.execute(
            select(WorkflowExecution).where(WorkflowExecution.client_id == client_id)
        )
        result["data_status"]["execution_count"] = len(execution_count.scalars().all())
        
        # Check sync state
        sync_state_stmt = select(SyncState).where(SyncState.client_id == client_id)
        sync_state_result = await db.execute(sync_state_stmt)
        sync_state = sync_state_result.scalar_one_or_none()
        
        if sync_state:
            result["data_status"]["last_workflow_sync"] = sync_state.last_workflow_sync
            result["data_status"]["last_execution_sync"] = sync_state.last_execution_sync
            result["data_status"]["total_workflows_synced"] = sync_state.total_workflows_synced
            result["data_status"]["total_executions_synced"] = sync_state.total_executions_synced
            
            if sync_state.last_error:
                result["warnings"].append(f"Last sync error: {sync_state.last_error}")
        else:
            result["warnings"].append("No sync state found - client has never been synced")
        
        return result
    
    def validate_client_configuration_sync(self, db: Session, client_id: str) -> Dict[str, Any]:
        """Synchronous version for Celery tasks"""
        result = {
            "client_id": client_id,
            "is_valid": True,
            "issues": [],
            "warnings": [],
            "data_status": {}
        }
        
        # Get client
        client = db.query(Client).filter(Client.id == client_id).first()
        
        if not client:
            result["is_valid"] = False
            result["issues"].append("Client not found")
            return result
        
        # Check n8n API configuration
        if not client.n8n_api_url:
            result["is_valid"] = False
            result["issues"].append("Missing n8n API URL")
        
        if not client.n8n_api_key_encrypted:
            result["is_valid"] = False
            result["issues"].append("Missing n8n API key")
        
        # Check data status
        workflow_count = db.query(Workflow).filter(Workflow.client_id == client_id).count()
        result["data_status"]["workflow_count"] = workflow_count
        
        execution_count = db.query(WorkflowExecution).filter(WorkflowExecution.client_id == client_id).count()
        result["data_status"]["execution_count"] = execution_count
        
        # Check sync state
        sync_state = db.query(SyncState).filter(SyncState.client_id == client_id).first()
        
        if sync_state:
            result["data_status"]["last_workflow_sync"] = sync_state.last_workflow_sync
            result["data_status"]["last_execution_sync"] = sync_state.last_execution_sync
            result["data_status"]["total_workflows_synced"] = sync_state.total_workflows_synced
            result["data_status"]["total_executions_synced"] = sync_state.total_executions_synced
            
            if sync_state.last_error:
                result["warnings"].append(f"Last sync error: {sync_state.last_error}")
        else:
            result["warnings"].append("No sync state found - client has never been synced")
        
        return result
    
    async def fix_client_configuration_issues(self, db: AsyncSession, client_id: str) -> Dict[str, Any]:
        """Attempt to fix common client configuration issues"""
        result = {
            "client_id": client_id,
            "fixes_applied": [],
            "manual_actions_required": []
        }
        
        # Get client
        stmt = select(Client).where(Client.id == client_id)
        client_result = await db.execute(stmt)
        client = client_result.scalar_one_or_none()
        
        if not client:
            result["manual_actions_required"].append("Client not found - cannot fix")
            return result
        
        # Reset stale sync state if needed
        sync_state_stmt = select(SyncState).where(SyncState.client_id == client_id)
        sync_state_result = await db.execute(sync_state_stmt)
        sync_state = sync_state_result.scalar_one_or_none()
        
        if sync_state and sync_state.last_error:
            sync_state.last_error = None
            sync_state.last_error_at = None
            result["fixes_applied"].append("Cleared sync error state")
        
        # Clear stale cache
        try:
            from app.services.cache.redis import redis_client
            cache_patterns = [
                f"*{client_id}*",
                f"enhanced_client_metrics:{client_id}",
                f"client_metrics:{client_id}",
                f"metrics_cache:*{client_id}*"
            ]
            
            for pattern in cache_patterns:
                await redis_client.clear_pattern(pattern)
            
            result["fixes_applied"].append("Cleared stale cache data")
        except Exception as e:
            result["manual_actions_required"].append(f"Manual cache clear needed: {str(e)}")
        
        # Check for missing n8n configuration
        if not client.n8n_api_url or not client.n8n_api_key_encrypted:
            result["manual_actions_required"].append(
                "n8n API configuration missing - admin must reconfigure n8n API URL and key"
            )
        
        await db.commit()
        return result
    
    def _generate_recommendations(self, validation_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        if validation_results["invalid_clients"]:
            recommendations.append(
                f"Reconfigure n8n API settings for {len(validation_results['invalid_clients'])} clients"
            )
        
        # Check for common issues
        missing_api_url = sum(1 for client in validation_results["invalid_clients"] 
                             if "Missing n8n API URL" in client["issues"])
        if missing_api_url > 0:
            recommendations.append(f"Set n8n API URL for {missing_api_url} clients")
        
        missing_api_key = sum(1 for client in validation_results["invalid_clients"] 
                             if "Missing n8n API key" in client["issues"])
        if missing_api_key > 0:
            recommendations.append(f"Set n8n API key for {missing_api_key} clients")
        
        if validation_results["total_clients"] > validation_results["valid_clients"]:
            recommendations.append("Run client configuration fix command for invalid clients")
        
        return recommendations


# Global instance
client_validator = ClientConfigurationValidator()