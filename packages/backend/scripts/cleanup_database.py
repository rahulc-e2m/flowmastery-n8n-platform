#!/usr/bin/env python3
"""
Clean up database by removing workflows that are no longer returned by n8n API
"""

import asyncio
import logging
from typing import Set

# Setup path for imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db
from app.services.client_service import ClientService
from app.services.persistent_metrics import persistent_metrics_collector
from app.models import Workflow, WorkflowExecution
from sqlalchemy import select, delete

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def cleanup_database():
    """Clean up database by removing archived workflows"""
    
    async for db in get_db():
        try:
            logger.info("=== Cleaning Up Database ===")
            
            client_service = ClientService()
            clients = await client_service.get_all_clients(db)
            
            total_removed_workflows = 0
            total_removed_executions = 0
            
            for client in clients:
                try:
                    logger.info(f"Processing client: {client.name}")
                    
                    # Get API key
                    api_key = await ClientService.get_n8n_api_key(db, client.id)
                    if not api_key or not client.n8n_api_url:
                        logger.info(f"  Skipping - no n8n config")
                        continue
                    
                    # Get current workflows from n8n (with archived filter)
                    try:
                        current_workflows = await persistent_metrics_collector._fetch_n8n_workflows(
                            client.n8n_api_url, api_key
                        )
                        current_workflow_ids = {str(wf.get('id')) for wf in current_workflows}
                        logger.info(f"  Current active workflows in n8n: {len(current_workflow_ids)}")
                    except Exception as e:
                        logger.error(f"  Failed to fetch workflows from n8n: {e}")
                        continue
                    
                    # Get workflows from database
                    db_workflows_stmt = select(Workflow).where(Workflow.client_id == client.id)
                    db_workflows_result = await db.execute(db_workflows_stmt)
                    db_workflows = db_workflows_result.scalars().all()
                    logger.info(f"  Workflows in database: {len(db_workflows)}")
                    
                    # Find workflows to remove (in DB but not in current n8n response)
                    workflows_to_remove = []
                    for db_workflow in db_workflows:
                        if db_workflow.n8n_workflow_id not in current_workflow_ids:
                            workflows_to_remove.append(db_workflow)
                    
                    if workflows_to_remove:
                        logger.info(f"  Removing {len(workflows_to_remove)} archived workflows")
                        
                        for workflow in workflows_to_remove:
                            logger.info(f"    - {workflow.name} (ID: {workflow.n8n_workflow_id})")
                            
                            # Count and remove executions first
                            executions_stmt = select(WorkflowExecution).where(
                                WorkflowExecution.workflow_id == workflow.id
                            )
                            executions_result = await db.execute(executions_stmt)
                            executions = executions_result.scalars().all()
                            
                            if executions:
                                logger.info(f"      Removing {len(executions)} executions")
                                for execution in executions:
                                    await db.delete(execution)
                                total_removed_executions += len(executions)
                            
                            # Remove the workflow
                            await db.delete(workflow)
                            total_removed_workflows += 1
                    else:
                        logger.info(f"  No archived workflows to remove")
                
                except Exception as e:
                    logger.error(f"Error processing client {client.name}: {e}")
                    continue
            
            # Commit all changes
            await db.commit()
            
            logger.info("=== Cleanup Results ===")
            logger.info(f"Removed workflows: {total_removed_workflows}")
            logger.info(f"Removed executions: {total_removed_executions}")
            
            # Verify final counts
            total_workflows_stmt = select(Workflow)
            total_workflows_result = await db.execute(total_workflows_stmt)
            remaining_workflows = len(total_workflows_result.scalars().all())
            logger.info(f"Remaining workflows in database: {remaining_workflows}")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            await db.rollback()
            raise
        finally:
            break


async def main():
    """Main function"""
    await cleanup_database()


if __name__ == "__main__":
    asyncio.run(main())