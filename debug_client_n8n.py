#!/usr/bin/env python3
"""Debug script to test client n8n API connection"""

import asyncio
import httpx
import sys
import os
sys.path.append('packages/backend')

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.client_service import ClientService

async def debug_client_n8n(client_id: int = 1):
    """Debug n8n connection for a specific client"""
    print(f"🔍 Debugging n8n connection for client {client_id}")
    
    # Get database session
    async for db in get_db():
        try:
            # Get client details
            client = await ClientService.get_client_by_id(db, client_id)
            if not client:
                print(f"❌ Client {client_id} not found")
                return
            
            print(f"📋 Client: {client.name}")
            print(f"🔗 n8n URL: {client.n8n_api_url}")
            
            # Get API key
            api_key = await ClientService.get_n8n_api_key(db, client_id)
            if not api_key:
                print("❌ No API key found for client")
                return
            
            print(f"🔑 API Key: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else '***'}")
            
            if not client.n8n_api_url:
                print("❌ No n8n URL configured for client")
                return
            
            # Test connection
            async with httpx.AsyncClient(timeout=10.0) as http_client:
                print("\n🧪 Testing API endpoints...")
                
                # Test workflows endpoint
                try:
                    print("📊 Testing /workflows endpoint...")
                    response = await http_client.get(
                        f"{client.n8n_api_url}/workflows",
                        headers={'X-N8N-API-KEY': api_key}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        workflows = data.get('data', [])
                        print(f"✅ Workflows: Found {len(workflows)} workflows")
                        
                        # Show first few workflows
                        for i, workflow in enumerate(workflows[:3]):
                            name = workflow.get('name', 'Unnamed')
                            active = workflow.get('active', False)
                            status = "🟢 Active" if active else "🔴 Inactive"
                            print(f"   {i+1}. {name} - {status}")
                    else:
                        print(f"❌ Workflows endpoint failed: {response.status_code}")
                        print(f"Response: {response.text}")
                        
                except Exception as e:
                    print(f"❌ Workflows endpoint error: {e}")
                
                # Test executions endpoint
                try:
                    print("\n⚡ Testing /executions endpoint...")
                    response = await http_client.get(
                        f"{client.n8n_api_url}/executions",
                        headers={'X-N8N-API-KEY': api_key},
                        params={'limit': 5}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        executions = data.get('data', [])
                        print(f"✅ Executions: Found {len(executions)} recent executions")
                        
                        # Show execution details
                        for i, execution in enumerate(executions):
                            workflow_id = execution.get('workflowId', 'Unknown')
                            status = execution.get('status', 'unknown')
                            started = execution.get('startedAt', 'Unknown')
                            print(f"   {i+1}. Workflow {workflow_id} - {status} - {started}")
                    else:
                        print(f"❌ Executions endpoint failed: {response.status_code}")
                        print(f"Response: {response.text}")
                        
                except Exception as e:
                    print(f"❌ Executions endpoint error: {e}")
                
                # Test basic health
                try:
                    print("\n🏥 Testing basic connectivity...")
                    response = await http_client.get(
                        f"{client.n8n_api_url.replace('/api/v1', '')}/healthz",
                        timeout=5.0
                    )
                    if response.status_code == 200:
                        print("✅ n8n instance is healthy")
                    else:
                        print(f"⚠️ Health check returned: {response.status_code}")
                except Exception as e:
                    print(f"⚠️ Health check failed: {e}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            await db.close()
            break

if __name__ == "__main__":
    client_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    asyncio.run(debug_client_n8n(client_id))