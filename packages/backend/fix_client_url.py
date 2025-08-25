#!/usr/bin/env python3
"""Fix client n8n URL in database"""

import asyncio
import sys
sys.path.append('.')

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.client_service import ClientService

async def fix_client_url(client_id: int = 1):
    """Fix the n8n URL for a client"""
    print(f"🔧 Fixing n8n URL for client {client_id}")
    
    async for db in get_db():
        try:
            client = await ClientService.get_client_by_id(db, client_id)
            if not client:
                print(f"❌ Client {client_id} not found")
                return
            
            print(f"📋 Client: {client.name}")
            print(f"🔗 Current URL: {client.n8n_api_url}")
            
            # Fix the URL
            correct_url = "https://n8n.sitepreviews.dev/api/v1"
            client.n8n_api_url = correct_url
            
            await db.commit()
            
            print(f"✅ Updated URL to: {correct_url}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            await db.close()
            break

if __name__ == "__main__":
    client_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    asyncio.run(fix_client_url(client_id))