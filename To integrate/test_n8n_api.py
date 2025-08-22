#!/usr/bin/env python3
"""
Test script to verify n8n API connection works.
This tests the core n8n API functionality without using OpenAI.
"""

import requests
import json
from config import N8N_API_URL, N8N_API_KEY

def test_n8n_connection():
    """Test basic n8n API connection"""
    headers = {
        "accept": "application/json",
        "X-N8N-API-KEY": N8N_API_KEY,
        "Content-Type": "application/json",
    }
    
    # Test the workflows endpoint
    url = f"{N8N_API_URL}/workflows"
    
    print("🔗 Testing n8n API connection...")
    print(f"URL: {url}")
    print(f"API Key: {N8N_API_KEY[:20]}...")
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ n8n API connection successful!")
            print(f"Response type: {type(data)}")
            
            if isinstance(data, dict) and "data" in data:
                workflows = data["data"]
                print(f"Number of workflows: {len(workflows)}")
                
                if workflows:
                    print("\n📋 Sample workflows:")
                    for i, wf in enumerate(workflows[:3]):  # Show first 3
                        print(f"  {i+1}. {wf.get('name', 'Unnamed')} (ID: {wf.get('id', 'N/A')})")
                else:
                    print("No workflows found.")
            else:
                print("Response format:", json.dumps(data, indent=2)[:500] + "...")
                
        else:
            print(f"❌ API request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    test_n8n_connection()
