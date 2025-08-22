#!/usr/bin/env python3
"""
Debug script to identify the issue with fast metrics
"""

import time
from n8n_metrics import N8nMetricsService
from config import N8N_API_URL, N8N_API_KEY
import traceback

def debug_fast_metrics():
    print("Debugging fast metrics issue...")
    
    # Create metrics service instance
    service = N8nMetricsService()
    
    # Configure with n8n credentials
    if not service.configure(N8N_API_URL, N8N_API_KEY):
        print("❌ Failed to connect to n8n")
        return
    
    print("✅ Connected to n8n successfully")
    
    # Debug individual components of fast metrics
    print("\n🔍 Testing individual API endpoints used in fast metrics...")
    
    try:
        print("   Testing workflows endpoint...")
        result = service._fetch_single_metric('/workflows', {'limit': 250})
        if result["success"]:
            workflows_data = result["data"]
            workflows = workflows_data.get('data', []) if isinstance(workflows_data, dict) else workflows_data
            print(f"   ✅ Workflows: {len(workflows)} retrieved")
        else:
            print(f"   ❌ Workflows failed: {result.get('error')}")
    except Exception as e:
        print(f"   ❌ Workflows exception: {e}")
        traceback.print_exc()
    
    try:
        print("   Testing executions endpoint...")
        result = service._fetch_single_metric('/executions', {'limit': 100})
        if result["success"]:
            executions_data = result["data"]
            executions = executions_data.get('data', []) if isinstance(executions_data, dict) else executions_data
            print(f"   ✅ Executions: {len(executions)} retrieved")
        else:
            print(f"   ❌ Executions failed: {result.get('error')}")
    except Exception as e:
        print(f"   ❌ Executions exception: {e}")
        traceback.print_exc()
    
    try:
        print("   Testing users endpoint...")
        result = service._fetch_single_metric('/users', {'limit': 100})
        if result["success"]:
            users_data = result["data"]
            users = users_data.get('data', []) if isinstance(users_data, dict) else users_data
            print(f"   ✅ Users: {len(users)} retrieved")
        else:
            print(f"   ❌ Users failed: {result.get('error')}")
    except Exception as e:
        print(f"   ❌ Users exception: {e}")
        traceback.print_exc()
    
    try:
        print("   Testing variables endpoint...")
        result = service._fetch_single_metric('/variables', {'limit': 50})
        if result["success"]:
            variables_data = result["data"]
            variables = variables_data.get('data', []) if isinstance(variables_data, dict) else variables_data
            print(f"   ✅ Variables: {len(variables)} retrieved")
        else:
            print(f"   ❌ Variables failed: {result.get('error')}")
    except Exception as e:
        print(f"   ❌ Variables exception: {e}")
        traceback.print_exc()
    
    # Now try the full fast metrics
    print(f"\n🚀 Testing full fast metrics method...")
    try:
        fast_metrics = service.get_fast_metrics()
        print(f"   Status: {fast_metrics.get('status')}")
        if fast_metrics.get('status') == 'error':
            print(f"   Error: {fast_metrics.get('error')}")
        elif fast_metrics.get('status') == 'success':
            workflows = fast_metrics.get("workflows", {})
            users = fast_metrics.get("users", {})
            print(f"   ✅ Success: {workflows.get('total_workflows', 0)} workflows, {users.get('total_users', 0)} users")
    except Exception as e:
        print(f"   ❌ Exception in get_fast_metrics: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    debug_fast_metrics()
