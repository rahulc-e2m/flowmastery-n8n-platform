#!/usr/bin/env python3
"""Test script to verify n8n metrics service functionality"""

from n8n_metrics import metrics_service
from config import N8N_API_URL, N8N_API_KEY

print("Testing n8n metrics service...")
print(f"API URL: {N8N_API_URL}")
print(f"API Key: {'*' * (len(N8N_API_KEY) - 8) + N8N_API_KEY[-8:]}")

print("\nTesting connection...")
result = metrics_service.configure(N8N_API_URL, N8N_API_KEY)
print(f"Connection result: {result}")

if result:
    print("\nGetting fast metrics...")
    metrics = metrics_service.get_fast_metrics()
    print(f"Metrics status: {metrics.get('status', 'unknown')}")
    
    if metrics.get('status') == 'success':
        workflows = metrics.get('workflows', {})
        executions = metrics.get('executions', {})
        users = metrics.get('users', {})
        
        print(f"Total workflows: {workflows.get('total_workflows', 0)}")
        print(f"Active workflows: {workflows.get('active_workflows', 0)}")
        print(f"Today executions: {executions.get('today_executions', 0)}")
        print(f"Success rate: {executions.get('success_rate', 0)}%")
        print(f"Total users: {users.get('total_users', 0)}")
        print(f"Response time: {metrics.get('response_time', 0)}s")
    else:
        print(f"Error: {metrics.get('error', 'Unknown error')}")
else:
    print("Failed to connect to n8n API")
