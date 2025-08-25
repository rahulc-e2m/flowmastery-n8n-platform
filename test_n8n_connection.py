#!/usr/bin/env python3
"""Simple script to test n8n API connection"""

import asyncio
import httpx
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_n8n_connection():
    """Test n8n API connection"""
    api_url = os.getenv('N8N_API_URL')
    api_key = os.getenv('N8N_API_KEY')
    
    if not api_url or not api_key:
        print("❌ Missing N8N_API_URL or N8N_API_KEY in .env file")
        return False
    
    print(f"🔗 Testing connection to: {api_url}")
    print(f"🔑 API Key: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else '***'}")
    
    try:
        async with httpx.AsyncClient() as client:
            # Test with /workflows endpoint
            response = await client.get(
                f"{api_url}/workflows",
                headers={
                    'X-N8N-API-KEY': api_key,
                    'Accept': 'application/json'
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                workflow_count = len(data.get('data', []))
                print(f"✅ Connection successful!")
                print(f"📊 Found {workflow_count} workflows")
                return True
            else:
                print(f"❌ API Error: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_n8n_connection())