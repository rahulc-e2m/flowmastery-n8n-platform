#!/usr/bin/env python3
"""
Script to force a complete re-sync of all workflows.
This will use the updated filtering logic to exclude archived workflows.
"""

import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession

# Setup path for imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db
from app.services.persistent_metrics import persistent_metrics_collector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def force_resync_all_workflows():
    """Force a complete re-sync of all client workflows"""
    
    async for db in get_db():
        try:
            logger.info("Starting forced workflow re-sync for all clients...")
            
            # Use the persistent metrics collector to sync all clients
            # This will use our updated filtering logic
            result = await persistent_metrics_collector.sync_all_clients(db)
            
            logger.info("Re-sync completed!")
            logger.info(f"Results: {result}")
            
        except Exception as e:
            logger.error(f"Error during re-sync: {e}")
            raise
        finally:
            break  # Exit the async generator


async def main():
    """Main function"""
    logger.info("Starting forced workflow re-sync...")
    await force_resync_all_workflows()
    logger.info("Re-sync completed!")


if __name__ == "__main__":
    asyncio.run(main())