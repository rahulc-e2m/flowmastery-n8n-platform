#!/usr/bin/env python3
"""
Force sync all clients by calling sync_client_data directly
"""

import asyncio
import logging

# Setup path for imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db
from app.services.persistent_metrics import persistent_metrics_collector
from app.services.client_service import ClientService
from app.services.cache.redis import redis_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def force_sync_all():
    """Force sync all clients individually"""
    
    async for db in get_db():
        try:
            logger.info("=== Force Syncing All Clients ===")
            
            # Clear caches first
            cache_patterns = [
                "all_workflows:*", "user_workflows:*", "workflow:*", "workflows:*",
                "client_workflows:*", "workflow_cache:*", "enhanced_client_metrics:*",
                "client_metrics:*", "admin_metrics:*", "metrics_cache:*",
                "fast_metrics", "dashboard_metrics_*"
            ]
            
            for pattern in cache_patterns:
                await redis_client.clear_pattern(pattern)
            
            # Get all clients
            client_service = ClientService()
            clients = await client_service.get_all_clients(db)
            
            logger.info(f"Found {len(clients)} clients to sync")
            
            results = {"synced_clients": 0, "errors": [], "total_workflows": 0, "total_executions": 0}
            
            for client in clients:
                try:
                    logger.info(f"Syncing client: {client.name}")
                    
                    # Call sync_client_data directly for each client
                    client_result = await persistent_metrics_collector.sync_client_data(db, client.id)
                    
                    results["synced_clients"] += 1
                    results["total_workflows"] += client_result.get("workflows_synced", 0)
                    results["total_executions"] += client_result.get("executions_synced", 0)
                    
                    logger.info(f"✅ {client.name}: {client_result.get('workflows_synced', 0)} workflows, {client_result.get('executions_synced', 0)} executions")
                    
                except Exception as e:
                    error_msg = f"Failed to sync client {client.name}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
            
            # Clear caches again
            for pattern in cache_patterns:
                await redis_client.clear_pattern(pattern)
            
            logger.info("=== Sync Results ===")
            logger.info(f"Synced clients: {results['synced_clients']}")
            logger.info(f"Total workflows: {results['total_workflows']}")
            logger.info(f"Total executions: {results['total_executions']}")
            logger.info(f"Errors: {len(results['errors'])}")
            
            for error in results["errors"]:
                logger.error(f"  - {error}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error during force sync: {e}")
            raise
        finally:
            break


async def main():
    """Main function"""
    await force_sync_all()


if __name__ == "__main__":
    asyncio.run(main())