#!/usr/bin/env python3
"""Detailed debug script for n8n API"""

import asyncio
import httpx
import sys
import os
sys.path.append('.')

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.client_service import ClientService

async def debug_n8n_detailed(client_id: int = 1):
    """Detailed debug of n8n API"""
    print(f"🔍 Detailed n8n API debug for client {client_id}")
    
    async for db in get_db():
        try:
            client = await ClientService.get_client_by_id(db, client_id)
            if not client:
                print(f"❌ Client {client_id} not found")
                return
            
            api_key = await ClientService.get_n8n_api_key(db, client_id)
            if not api_key or not client.n8n_api_url:
                print("❌ Missing API key or URL")
                return
            
            print(f"📋 Client: {client.name}")
            print(f"🔗 Stored URL: {client.n8n_api_url}")
            print(f"🔑 API Key: {api_key[:10]}...{api_key[-4:]}")
            
            # Test different URL formats
            test_urls = [
                client.n8n_api_url,  # As stored
                client.n8n_api_url.rstrip('/'),  # Remove trailing slash
                client.n8n_api_url.replace('/api/v1', '') + '/api/v1',  # Ensure /api/v1
                'https://n8n.sitepreviews.dev/api/v1',  # Direct format
            ]
            
            async with httpx.AsyncClient(timeout=15.0) as http_client:
                for i, test_url in enumerate(test_urls):
                    print(f"\n🧪 Test {i+1}: {test_url}")
                    
                    try:
                        # Test workflows endpoint
                        response = await http_client.get(
                            f"{test_url}/workflows",
                            headers={
                                'X-N8N-API-KEY': api_key,
                                'Accept': 'application/json',
                                'Content-Type': 'application/json'
                            }
                        )
                        
                        print(f"   Status: {response.status_code}")
                        print(f"   Headers: {dict(response.headers)}")
                        print(f"   Content-Type: {response.headers.get('content-type', 'unknown')}")
                        
                        if response.status_code == 200:
                            try:
                                data = response.json()
                                workflows = data.get('data', []) if isinstance(data, dict) else data
                                print(f"   ✅ Success: {len(workflows)} workflows found")
                                if workflows:
                                    print(f"   First workflow: {workflows[0].get('name', 'Unnamed')}")
                                break
                            except Exception as json_error:
                                print(f"   ❌ JSON parse error: {json_error}")
                                print(f"   Raw response: {response.text[:200]}...")
                        else:
                            print(f"   ❌ Error response: {response.text[:200]}...")
                            
                    except Exception as e:
                        print(f"   ❌ Request error: {e}")
                
                # Also test the base n8n instance
                print(f"\n🏥 Testing base instance health...")
                try:
                    base_url = client.n8n_api_url.replace('/api/v1', '')
                    response = await http_client.get(f"{base_url}/healthz")
                    print(f"   Health check: {response.status_code}")
                    if response.status_code == 200:
                        print(f"   Response: {response.text}")
                except Exception as e:
                    print(f"   Health check error: {e}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            await db.close()
            break

if __name__ == "__main__":
    client_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    asyncio.run(debug_n8n_detailed(client_id))