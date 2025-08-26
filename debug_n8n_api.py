#!/usr/bin/env python3
"""
Debug script to inspect n8n API responses
"""

import requests
import json
import sys

def test_n8n_api():
    """Test n8n API directly to see what data we get"""
    
    # Get client info from our API first
    BASE_URL = "http://localhost:8000"
    
    # Authenticate
    auth_response = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
        "email": "admin@example.com",
        "password": "admin123"
    })
    
    if auth_response.status_code != 200:
        print("❌ Authentication failed")
        return
    
    token = auth_response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get client info
    clients_response = requests.get(f"{BASE_URL}/api/v1/clients", headers=headers)
    if clients_response.status_code != 200:
        print("❌ Failed to get clients")
        return
    
    clients = clients_response.json()
    if not clients:
        print("❌ No clients found")
        return
    
    client = clients[0]
    n8n_url = client.get('n8n_api_url')
    
    if not n8n_url:
        print("❌ No n8n URL configured")
        return
    
    print(f"🔍 Testing n8n API: {n8n_url}")
    
    # Use the provided API key
    n8n_api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzNTk3OTkxYy01MTkzLTRlMmUtYTYzZS05MDJlN2Q5NGNkNzUiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzU2MTk5NTY5fQ.Vp9J4yWBwjvF_88wbuZorHlzxFRSOg0GgAm8bby3y88"
    
    try:
        # Test executions endpoint
        exec_url = f"{n8n_url}/executions"
        print(f"📡 Fetching: {exec_url}")
        
        # Use proper authentication
        n8n_headers = {
            'X-N8N-API-KEY': n8n_api_key,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(exec_url, params={'limit': 5}, headers=n8n_headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}...")
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and 'data' in data:
                executions = data['data']
            else:
                executions = data if isinstance(data, list) else [data]
            
            print(f"\n📊 Found {len(executions)} executions")
            
            for i, exec_data in enumerate(executions[:3]):  # Show first 3
                print(f"\n🔍 Execution {i+1}:")
                print(f"  ID: {exec_data.get('id')}")
                print(f"  Status: '{exec_data.get('status')}'")
                print(f"  Mode: '{exec_data.get('mode')}'")
                print(f"  Finished: {exec_data.get('finished')}")
                print(f"  Started: {exec_data.get('startedAt')}")
                print(f"  Stopped: {exec_data.get('stoppedAt')}")
                print(f"  Workflow ID: {exec_data.get('workflowId')}")
                
                # Show all keys
                print(f"  All keys: {list(exec_data.keys())}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_n8n_api()