from n8n_metrics import metrics_service
from config import N8N_API_URL, N8N_API_KEY

print("Testing fast metrics with debug output...")
result = metrics_service.configure(N8N_API_URL, N8N_API_KEY)
if result:
    print("Connection successful, testing fast metrics...")
    fast_metrics = metrics_service.get_fast_metrics()
    print(f"Fast metrics status: {fast_metrics.get('status')}")
    if fast_metrics.get('status') == 'error':
        print(f"Error: '{fast_metrics.get('error')}'")
        print(f"Error length: {len(fast_metrics.get('error', ''))}")
    else:
        print("Success!")
        workflows = fast_metrics.get('workflows', {})
        print(f"Total workflows: {workflows.get('total_workflows', 0)}")
else:
    print('Connection failed')
