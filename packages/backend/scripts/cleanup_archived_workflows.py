#!/usr/bin/env python3
"""
Script to clean up archived workflows from the database.
This script will remove workflows that are no longer returned by the n8n API
(likely because they are archived).
"""

import asyncio
import logging
from typing import Set, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

# Setup path for imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db
from app.models import Client, Workflow, WorkflowExecution
from app.services.client_service import ClientService
from app.services.persistent_metrics import persistent_metrics_collector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def cleanup_archived_workflows():
    """Clean up archived workflows from the database"""
    
    async for db in get_db():
        try:
            # Get all clients with n8n configuration
            clients = await ClientService.get_all_clients(db)
            
            total_removed_workflows = 0
            total_removed_executions = 0
            
            for client in clients:
                if not client.n8n_api_url or not client.n8n_api_key_encrypted:
                    logger.info(f"Skipping client {client.name} - no n8n configuration")
                    continue
                
                try:
                    logger.info(f"Processing client: {client.name}")
                    
                    # Get API key
                    api_key = await ClientService.get_n8n_api_key(db, client.id)
                    if not api_key:
                        logger.warning(f"No API key for client {client.name}")
                        continue
                    
                    # Fetch current workflows from n8n (with archived filter)
                    current_workflows = await persistent_metrics_collector._fetch_n8n_workflows(
                        client.n8n_api_url, api_key
                    )
                    current_workflow_ids = {str(wf.get('id')) for wf in current_workflows}
                    
                    logger.info(f"Found {len(current_workflow_ids)} active workflows in n8n for {client.name}")
                    
                    # Get workflows from database
                    db_workflows_stmt = select(Workflow).where(Workflow.client_id == client.id)
                    db_workflows_result = await db.execute(db_workflows_stmt)
                    db_workflows = db_workflows_result.scalars().all()
                    
                    logger.info(f"Found {len(db_workflows)} workflows in database for {client.name}")
                    
                    # Find workflows to remove (in DB but not in current n8n response)
                    workflows_to_remove = []
                    for db_workflow in db_workflows:
                        if db_workflow.n8n_workflow_id not in current_workflow_ids:
                            workflows_to_remove.append(db_workflow)
                    
                    if workflows_to_remove:
                        logger.info(f"Found {len(workflows_to_remove)} archived workflows to remove for {client.name}")
                        
                        for workflow in workflows_to_remove:
                            logger.info(f"  - Removing workflow: {workflow.name} (ID: {workflow.n8n_workflow_id})")
                            
                            # Count executions that will be removed
                            executions_count_stmt = select(WorkflowExecution).where(
                                WorkflowExecution.workflow_id == workflow.id
                            )
                            executions_result = await db.execute(executions_count_stmt)
                            executions_count = len(executions_result.scalars().all())
                            
                            if executions_count > 0:
                                logger.info(f"    - Will also remove {executions_count} executions")
                                total_removed_executions += executions_count
                            
                            # Remove the workflow (executions will be cascade deleted)
                            await db.delete(workflow)
                            total_removed_workflows += 1
                    else:
                        logger.info(f"No archived workflows found for {client.name}")
                
                except Exception as e:
                    logger.error(f"Error processing client {client.name}: {e}")
                    continue
            
            # Commit all changes
            await db.commit()
            
            logger.info(f"Cleanup completed:")
            logger.info(f"  - Removed {total_removed_workflows} archived workflows")
            logger.info(f"  - Removed {total_removed_executions} associated executions")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            await db.rollback()
            raise
        finally:
            break  # Exit the async generator


async def main():
    """Main function"""
    logger.info("Starting archived workflows cleanup...")
    await cleanup_archived_workflows()
    logger.info("Cleanup completed!")


if __name__ == "__main__":
    asyncio.run(main())