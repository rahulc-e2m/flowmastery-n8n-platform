#!/usr/bin/env python3
"""
Test the new execution API endpoints
"""

import requests
import json

def test_execution_apis():
    # Authenticate
    auth_response = requests.post('http://localhost:8000/api/v1/auth/login', json={
        'email': 'admin@example.com',
        'password': 'admin123'
    })

    if auth_response.status_code != 200:
        print('❌ Authentication failed')
        return

    token = auth_response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    print("🧪 Testing Execution API Endpoints")
    print("=" * 50)
    
    # Test execution stats endpoint
    print("\n📊 Testing Execution Stats...")
    response = requests.get('http://localhost:8000/api/v1/metrics/client/1/execution-stats', headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f'✅ Found {data["total_workflows"]} workflows with execution data')
        
        for workflow in data['workflow_stats'][:5]:
            print(f'  📈 {workflow["workflow_name"]}:')
            print(f'     - {workflow["total_executions"]} executions')
            print(f'     - {workflow["success_rate"]}% success rate')
            print(f'     - {workflow["avg_execution_time_seconds"]}s avg time')
            print(f'     - Active: {workflow["active"]}')
    else:
        print(f'❌ Execution Stats API failed: {response.status_code}')
        print(response.text[:200])
    
    # Test recent executions endpoint
    print("\n📋 Testing Recent Executions...")
    response = requests.get('http://localhost:8000/api/v1/metrics/client/1/executions?limit=10', headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f'✅ Found {data["total_count"]} recent executions')
        
        for execution in data['executions'][:5]:
            print(f'  🔄 {execution["n8n_execution_id"]}:')
            print(f'     - Workflow: {execution["workflow_name"]}')
            print(f'     - Status: {execution["status"]}')
            print(f'     - Duration: {execution["execution_time_seconds"]}s')
            print(f'     - Started: {execution["started_at"][:19] if execution["started_at"] else "N/A"}')
    else:
        print(f'❌ Recent Executions API failed: {response.status_code}')
        print(response.text[:200])

if __name__ == "__main__":
    test_execution_apis()