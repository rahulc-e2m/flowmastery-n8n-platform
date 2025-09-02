#!/usr/bin/env python3
"""
Simple script to fix archived workflows by triggering a re-sync
"""

import asyncio
import logging

# Setup path for imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db
from app.services.persistent_metrics import persistent_metrics_collector
from app.services.cache.redis import redis_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Main function to fix archived workflows"""
    logger.info("=== Starting Simple Archived Workflows Fix ===")
    
    try:
        # Clear workflow-related caches
        logger.info("Clearing caches...")
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
        
        logger.info("Caches cleared!")
        
        # Force re-sync using the persistent metrics collector
        async for db in get_db():
            try:
                logger.info("Starting workflow re-sync...")
                result = await persistent_metrics_collector.sync_all_clients(db)
                logger.info(f"Re-sync completed: {result}")
                break
            except Exception as e:
                logger.error(f"Error during re-sync: {e}")
                raise
        
        # Clear caches again
        logger.info("Clearing caches again...")
        for pattern in cache_patterns:
            await redis_client.clear_pattern(pattern)
        
        logger.info("=== Fix Completed Successfully ===")
        
    except Exception as e:
        logger.error(f"Fix failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())