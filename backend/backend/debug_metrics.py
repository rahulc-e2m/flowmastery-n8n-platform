#!/usr/bin/env python3
"""Debug script for n8n metrics service"""

from n8n_metrics import metrics_service
from config import N8N_API_URL, N8N_API_KEY
import traceback

print("Debugging n8n metrics service...")

# Test connection first
print("Testing connection...")
try:
    result = metrics_service.configure(N8N_API_URL, N8N_API_KEY)
    print(f"Connection result: {result}")
except Exception as e:
    print(f"Connection error: {e}")
    traceback.print_exc()
    exit(1)

if not result:
    print("Failed to connect")
    exit(1)

# Test individual metrics
print("\n1. Testing workflows metrics...")
try:
    workflow_metrics = metrics_service.get_workflows_metrics()
    print(f"Workflow metrics: {workflow_metrics}")
except Exception as e:
    print(f"Workflow error: {e}")
    traceback.print_exc()

print("\n2. Testing executions metrics...")
try:
    execution_metrics = metrics_service.get_executions_metrics(1)  # Just 1 day
    print(f"Execution metrics: {execution_metrics}")
except Exception as e:
    print(f"Execution error: {e}")
    traceback.print_exc()

print("\n3. Testing users metrics...")
try:
    user_metrics = metrics_service.get_users_metrics()
    print(f"User metrics: {user_metrics}")
except Exception as e:
    print(f"User error: {e}")
    traceback.print_exc()

print("\n4. Testing fast metrics...")
try:
    fast_metrics = metrics_service.get_fast_metrics()
    print(f"Fast metrics: {fast_metrics}")
except Exception as e:
    print(f"Fast metrics error: {e}")
    traceback.print_exc()
