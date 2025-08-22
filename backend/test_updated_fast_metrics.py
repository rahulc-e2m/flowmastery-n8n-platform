#!/usr/bin/env python3
"""
Test script to verify the updated fast metrics functionality
"""

import time
from n8n_metrics import N8nMetricsService
from config import N8N_API_URL, N8N_API_KEY

def test_fast_metrics():
    print("Testing updated fast metrics with higher limits...")
    
    # Create metrics service instance
    service = N8nMetricsService()
    
    # Configure with n8n credentials
    if not service.configure(N8N_API_URL, N8N_API_KEY):
        print("❌ Failed to connect to n8n")
        return
    
    print("✅ Connected to n8n successfully")
    
    # Test fast metrics
    print("\n🚀 Testing fast metrics (updated with higher limits)...")
    start_time = time.time()
    
    try:
        fast_metrics = service.get_fast_metrics()
        response_time = time.time() - start_time
        
        if fast_metrics.get("status") == "success":
            workflows = fast_metrics.get("workflows", {})
            users = fast_metrics.get("users", {})
            executions = fast_metrics.get("executions", {})
            
            print(f"✅ Fast metrics retrieved in {response_time:.2f} seconds")
            print(f"   📊 Workflows: {workflows.get('total_workflows', 0)} total, {workflows.get('active_workflows', 0)} active")
            print(f"   👥 Users: {users.get('total_users', 0)} total")
            print(f"   ⚡ Executions: {executions.get('total_executions', 0)} total")
            print(f"   📈 Response Time: {fast_metrics.get('response_time', 0)} seconds")
            
            # Compare with expected values
            expected_workflows = 243
            expected_users = 65
            actual_workflows = workflows.get('total_workflows', 0)
            actual_users = users.get('total_users', 0)
            
            print(f"\n🔍 Comparison with expected values:")
            print(f"   Workflows: {actual_workflows}/{expected_workflows} ({'✅ Match' if actual_workflows == expected_workflows else '⚠️  Partial' if actual_workflows > 50 else '❌ Low'})")
            print(f"   Users: {actual_users}/{expected_users} ({'✅ Match' if actual_users == expected_users else '⚠️  Partial' if actual_users > 10 else '❌ Low'})")
            
        else:
            print(f"❌ Fast metrics failed: {fast_metrics.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Exception during fast metrics test: {e}")
        
    # Test dashboard metrics for comparison
    print(f"\n🚀 Testing dashboard metrics (comprehensive)...")
    start_time = time.time()
    
    try:
        dashboard_metrics = service.get_comprehensive_metrics()
        response_time = time.time() - start_time
        
        if dashboard_metrics.get("status") == "success":
            workflows = dashboard_metrics.get("workflows", {})
            users = dashboard_metrics.get("users", {})
            
            print(f"✅ Dashboard metrics retrieved in {response_time:.2f} seconds")
            print(f"   📊 Workflows: {workflows.get('total_workflows', 0)} total, {workflows.get('active_workflows', 0)} active")
            print(f"   👥 Users: {users.get('total_users', 0)} total")
            print(f"   📈 Response Time: {dashboard_metrics.get('response_time', 0)} seconds")
            
        else:
            print(f"❌ Dashboard metrics failed: {dashboard_metrics.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Exception during dashboard metrics test: {e}")

if __name__ == "__main__":
    test_fast_metrics()
