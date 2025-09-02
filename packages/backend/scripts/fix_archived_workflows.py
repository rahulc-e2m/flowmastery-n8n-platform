#!/usr/bin/env python3
"""
Comprehensive script to fix archived workflows issue:
1. Clear all workflow-related caches
2. Force re-sync of workflows with new filtering
3. Clean up any remaining archived workflows
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
from app.services.cache.redis import redis_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def clear_workflow_caches():
    """Clear all workflow-related caches"""
    try:
        logger.info("Clearing workflow-related caches...")
        
        cache_patterns = [
            "all_workflows:*",
            "user_workflows:*", 
            "workflow:*",
            "workflows:*",
            "client_workflows:*",
            "workflow_cache:*",
            "enhanced_client_metrics:*",
            "client_metrics:*",
            "admin_metrics:*",
            "metrics_cache:*",
            "fast_metrics",
            "dashboard_metrics_*"
        ]
        
        for pattern in cache_patterns:
            await redis_client.clear_pattern(pattern)
            logger.info(f"Cleared cache pattern: {pattern}")
            
        logger.info("Cache clearing completed!")
        
    except Exception as e:
        logger.error(f"Error clearing caches: {e}")


async def force_workflow_resync():
    """Force a complete re-sync of workflows using updated filtering"""
    async for db in get_db():
        try:
            logger.info("Starting forced workflow re-sync...")
            
            # Sync all clients - this will use our updated filtering logic
            result = await persistent_metrics_collector.sync_all_clients(db)
            
            logger.info(f"Re-sync completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error during re-sync: {e}")
            raise
        finally:
            break


async def cleanup_orphaned_workflows():
    """Clean up any workflows that might still be archived"""
    async for db in get_db():
        try:
            logger.info("Checking for orphaned archived workflows...")
            
            clients = await ClientService.get_all_clients(db)
            total_removed = 0
            
            for client in clients:
                if not client.n8n_api_url or not client.n8n_api_key_encrypted:
                    continue
                
                try:
                    # Get API key
                    api_key = await ClientService.get_n8n_api_key(db, client.id)
                    if not api_key:
                        continue
                    
                    # Fetch current active workflows from n8n
                    current_workflows = await persistent_metrics_collector._fetch_n8n_workflows(
                        client.n8n_api_url, api_key
                    )
                    current_workflow_ids = {str(wf.get('id')) for wf in current_workflows}
                    
                    # Get workflows from database
                    db_workflows_stmt = select(Workflow).where(Workflow.client_id == client.id)
                    db_workflows_result = await db.execute(db_workflows_stmt)
                    db_workflows = db_workflows_result.scalars().all()
                    
                    # Find workflows to remove
                    workflows_to_remove = []
                    for db_workflow in db_workflows:
                        if db_workflow.n8n_workflow_id not in current_workflow_ids:
                            workflows_to_remove.append(db_workflow)
                    
                    if workflows_to_remove:
                        logger.info(f"Removing {len(workflows_to_remove)} orphaned workflows for {client.name}")
                        
                        for workflow in workflows_to_remove:
                            logger.info(f"  - Removing: {workflow.name}")
                            await db.delete(workflow)
                            total_removed += 1
                
                except Exception as e:
                    logger.error(f"Error processing client {client.name}: {e}")
                    continue
            
            if total_removed > 0:
                await db.commit()
                logger.info(f"Removed {total_removed} orphaned workflows")
            else:
                logger.info("No orphaned workflows found")
                
            return total_removed
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            await db.rollback()
            raise
        finally:
            break


async def verify_results():
    """Verify that archived workflows are no longer present"""
    async for db in get_db():
        try:
            logger.info("Verifying results...")
            
            clients = await ClientService.get_all_clients(db)
            
            for client in clients:
                if not client.n8n_api_url or not client.n8n_api_key_encrypted:
                    continue
                
                # Count workflows in database
                db_workflows_stmt = select(Workflow).where(Workflow.client_id == client.id)
                db_workflows_result = await db.execute(db_workflows_stmt)
                db_workflows = db_workflows_result.scalars().all()
                
                logger.info(f"Client {client.name}: {len(db_workflows)} workflows in database")
                
                # Try to get current workflows from n8n for comparison
                try:
                    api_key = await ClientService.get_n8n_api_key(db, client.id)
                    if api_key:
                        current_workflows = await persistent_metrics_collector._fetch_n8n_workflows(
                            client.n8n_api_url, api_key
                        )
                        logger.info(f"Client {client.name}: {len(current_workflows)} active workflows in n8n")
                except Exception as e:
                    logger.warning(f"Could not verify n8n workflows for {client.name}: {e}")
            
        except Exception as e:
            logger.error(f"Error during verification: {e}")
        finally:
            break


async def main():
    """Main function to fix archived workflows issue"""
    logger.info("=== Starting Archived Workflows Fix ===")
    
    try:
        # Step 1: Clear caches
        await clear_workflow_caches()
        
        # Step 2: Force re-sync with new filtering
        sync_result = await force_workflow_resync()
        
        # Step 3: Clean up any remaining orphaned workflows
        removed_count = await cleanup_orphaned_workflows()
        
        # Step 4: Clear caches again to ensure fresh data
        await clear_workflow_caches()
        
        # Step 5: Verify results
        await verify_results()
        
        logger.info("=== Fix Completed Successfully ===")
        logger.info(f"Sync result: {sync_result}")
        logger.info(f"Removed orphaned workflows: {removed_count}")
        
    except Exception as e:
        logger.error(f"Fix failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())