#!/usr/bin/env python3
"""
Debug script to check client configurations
"""

import asyncio
import logging

# Setup path for imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db
from app.services.client_service import ClientService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def debug_clients():
    """Debug client configurations"""
    
    async for db in get_db():
        try:
            logger.info("=== Debugging Client Configurations ===")
            
            client_service = ClientService()
            clients = await client_service.get_all_clients(db)
            
            logger.info(f"Found {len(clients)} clients:")
            
            for client in clients:
                logger.info(f"\nClient: {client.name} (ID: {client.id})")
                logger.info(f"  - n8n_api_url: {client.n8n_api_url}")
                logger.info(f"  - n8n_api_key_encrypted: {'SET' if client.n8n_api_key_encrypted else 'NOT SET'}")
                
                # Try to get the API key
                try:
                    api_key = await ClientService.get_n8n_api_key(db, client.id)
                    logger.info(f"  - API key retrieval: {'SUCCESS' if api_key else 'FAILED'}")
                    if api_key:
                        logger.info(f"  - API key length: {len(api_key)}")
                except Exception as e:
                    logger.error(f"  - API key retrieval ERROR: {e}")
                
                # Check the condition used in sync
                has_config = client.n8n_api_url and client.n8n_api_key_encrypted
                logger.info(f"  - Has n8n config: {has_config}")
            
        except Exception as e:
            logger.error(f"Error debugging clients: {e}")
            raise
        finally:
            break


async def main():
    """Main function"""
    await debug_clients()


if __name__ == "__main__":
    asyncio.run(main())