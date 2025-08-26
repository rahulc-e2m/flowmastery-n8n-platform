#!/usr/bin/env python3
"""
Debug script for Celery client metrics sync task
"""

import requests
import time
import json
import sys

BASE_URL = "http://localhost:8000"

# Authentication credentials
AUTH_EMAIL = "admin@example.com"
AUTH_PASSWORD = "admin123"

class APIClient:
    def __init__(self):
        self.token = None
        self.headers = None
        self._authenticate()
    
    def _authenticate(self):
        """Get authentication token"""
        try:
            response = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
                "email": AUTH_EMAIL,
                "password": AUTH_PASSWORD
            }, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.headers = {
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json"
                }
                print("✅ Authentication successful")
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"❌ Authentication error: {e}")
    
    def get(self, endpoint, **kwargs):
        """Make authenticated GET request"""
        return requests.get(f"{BASE_URL}{endpoint}", headers=self.headers, **kwargs)
    
    def post(self, endpoint, **kwargs):
        """Make authenticated POST request"""
        return requests.post(f"{BASE_URL}{endpoint}", headers=self.headers, **kwargs)

def test_celery_health(client):
    """Test basic Celery health"""
    print("🔍 Testing Celery Health...")
    if not client.headers:
        return False
        
    try:
        response = client.post("/api/v1/tasks/health-check", timeout=10)
        if response.status_code == 200:
            data = response.json()
            task_id = data.get('task_id')
            print(f"✅ Health check task started: {task_id}")
            
            # Wait and check result
            time.sleep(3)
            status_response = client.get(f"/api/v1/tasks/status/{task_id}", timeout=10)
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"✅ Task completed with status: {status_data['status']}")
                if status_data.get('result'):
                    print(f"📊 Result: {json.dumps(status_data['result'], indent=2)}")
                return True
            else:
                print(f"❌ Task status check failed: {status_response.status_code}")
                return False
        else:
            print(f"❌ Health check failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def get_clients(client):
    """Get list of clients"""
    print("🔍 Getting client list...")
    if not client.headers:
        return []
        
    try:
        response = client.get("/api/v1/clients", timeout=10)
        if response.status_code == 200:
            clients = response.json()
            print(f"✅ Found {len(clients)} clients")
            for c in clients:
                print(f"   - Client {c['id']}: {c['name']}")
                if c.get('n8n_api_url'):
                    print(f"     n8n URL: {c['n8n_api_url']}")
                else:
                    print(f"     ⚠️ No n8n URL configured")
            return clients
        else:
            print(f"❌ Failed to get clients: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error getting clients: {e}")
        return []

def test_client_sync(client, client_id):
    """Test syncing a specific client"""
    print(f"🔍 Testing client sync for client {client_id}...")
    if not client.headers:
        return False
        
    try:
        response = client.post(f"/api/v1/tasks/sync-client/{client_id}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            task_id = data.get('task_id')
            print(f"✅ Client sync task started: {task_id}")
            
            # Monitor task progress
            for i in range(30):  # Wait up to 30 seconds
                time.sleep(1)
                status_response = client.get(f"/api/v1/tasks/status/{task_id}", timeout=10)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data['status']
                    
                    if status == 'SUCCESS':
                        print(f"✅ Task completed successfully!")
                        result = status_data.get('result', {})
                        print(f"📊 Result: {json.dumps(result, indent=2)}")
                        return True
                    elif status == 'FAILURE':
                        print(f"❌ Task failed!")
                        error_info = status_data.get('result') or status_data.get('info', {})
                        print(f"❌ Error: {json.dumps(error_info, indent=2)}")
                        return False
                    elif status in ['PENDING', 'STARTED', 'RETRY']:
                        if i % 5 == 0:  # Print every 5 seconds
                            print(f"⏳ Still running... ({status})")
                        continue
                    else:
                        print(f"❓ Unknown status: {status}")
                        continue
                else:
                    print(f"❌ Status check failed: {status_response.status_code}")
                    return False
            
            print("⏰ Task timed out after 30 seconds")
            return False
            
        else:
            print(f"❌ Failed to start client sync: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Client sync error: {e}")
        return False

def test_all_clients_sync(client):
    """Test syncing all clients"""
    print("🔍 Testing sync for all clients...")
    if not client.headers:
        return False
        
    try:
        response = client.post("/api/v1/tasks/sync-all", timeout=10)
        if response.status_code == 200:
            data = response.json()
            task_id = data.get('task_id')
            print(f"✅ All clients sync task started: {task_id}")
            
            # Monitor task progress
            for i in range(60):  # Wait up to 60 seconds for all clients
                time.sleep(1)
                status_response = client.get(f"/api/v1/tasks/status/{task_id}", timeout=10)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data['status']
                    
                    if status == 'SUCCESS':
                        print(f"✅ All clients sync completed!")
                        result = status_data.get('result', {})
                        print(f"📊 Result: {json.dumps(result, indent=2)}")
                        return True
                    elif status == 'FAILURE':
                        print(f"❌ All clients sync failed!")
                        error_info = status_data.get('result') or status_data.get('info', {})
                        print(f"❌ Error: {json.dumps(error_info, indent=2)}")
                        return False
                    elif status in ['PENDING', 'STARTED', 'RETRY']:
                        if i % 10 == 0:  # Print every 10 seconds
                            print(f"⏳ Still running... ({status})")
                        continue
                    else:
                        print(f"❓ Unknown status: {status}")
                        continue
                else:
                    print(f"❌ Status check failed: {status_response.status_code}")
                    return False
            
            print("⏰ Task timed out after 60 seconds")
            return False
            
        else:
            print(f"❌ Failed to start all clients sync: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ All clients sync error: {e}")
        return False

def main():
    """Main debug function"""
    print("🐛 Celery Task Debug Script")
    print("=" * 50)
    
    # Initialize API client with authentication
    api_client = APIClient()
    if not api_client.headers:
        print("❌ Failed to authenticate. Check credentials.")
        sys.exit(1)
    
    # Test basic Celery health first
    if not test_celery_health(api_client):
        print("❌ Basic Celery health check failed. Check if Celery worker is running.")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    
    # Get clients
    clients = get_clients(api_client)
    if not clients:
        print("❌ No clients found or failed to get clients")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    
    # Test individual client sync
    if len(sys.argv) > 1:
        try:
            client_id = int(sys.argv[1])
            print(f"🎯 Testing specific client: {client_id}")
            test_client_sync(api_client, client_id)
        except ValueError:
            print("❌ Invalid client ID provided")
            sys.exit(1)
    else:
        # Test first client if available
        if clients:
            first_client = clients[0]
            print(f"🎯 Testing first client: {first_client['id']} ({first_client['name']})")
            test_client_sync(api_client, first_client['id'])
    
    print("\n" + "=" * 50)
    
    # Test all clients sync
    print("🎯 Testing all clients sync...")
    test_all_clients_sync(api_client)
    
    print("\n🔗 Useful commands:")
    print(f"   - Check Celery Flower: http://localhost:5555")
    print(f"   - API docs: {BASE_URL}/docs")
    print(f"   - Run for specific client: python debug_celery_task.py <client_id>")

if __name__ == "__main__":
    main()