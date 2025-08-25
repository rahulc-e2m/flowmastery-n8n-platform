#!/usr/bin/env python3
"""Test script to check n8n API connectivity"""

import asyncio
import httpx
from app.database import get_db
from app.services.client_service import ClientService

async def test_n8n_endpoints():
    async for db in get_db():
        try:
            client = await ClientService.get_client_by_id(db, 1)
            api_key = await ClientService.get_n8n_api_key(db, 1)
            base_url = client.n8n_api_url.rstrip('/')
            
            print(f"Testing n8n API for client: {client.name}")
            print(f"Base URL: {base_url}")
            print(f"API Key exists: {api_key is not None}")
            print()
            
            endpoints_to_test = [
                '/api/v1/workflows',
                '/rest/workflows', 
                '/webhook-test/workflows',
                '/api/workflows'
            ]
            
            async with httpx.AsyncClient() as http_client:
                for endpoint in endpoints_to_test:
                    try:
                        url = base_url + endpoint
                        print(f'Testing: {url}')
                        response = await http_client.get(
                            url,
                            headers={'X-N8N-API-KEY': api_key},
                            timeout=5.0
                        )
                        print(f'  Status: {response.status_code}')
                        content_type = response.headers.get('content-type', 'unknown')
                        print(f'  Content-Type: {content_type}')
                        
                        if 'json' in content_type:
                            try:
                                json_data = response.json()
                                print(f'  JSON Response: {json_data}')
                            except:
                                print(f'  JSON Parse Error')
                        else:
                            print(f'  Text Preview: {response.text[:100]}...')
                        print()
                    except Exception as e:
                        print(f'  Error: {str(e)}')
                        print()
            break
        except Exception as e:
            print(f'Error: {str(e)}')
            break

if __name__ == "__main__":
    asyncio.run(test_n8n_endpoints())