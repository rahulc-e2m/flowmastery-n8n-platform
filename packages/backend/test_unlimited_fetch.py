#!/usr/bin/env python3
"""Test unlimited workflow and execution fetching"""

import asyncio
import sys
sys.path.append('.')

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.client_service import ClientService
from app.services.metrics_service import MetricsService

async def test_unlimited_fetch(client_id: int = 1):
    """Test fetching all workflows and executions"""
    print(f"🧪 Testing unlimited fetch for client {client_id}")
    
    async for db in get_db():
        try:
            client = await ClientService.get_client_by_id(db, client_id)
            if not client:
                print(f"❌ Client {client_id} not found")
                return
            
            api_key = await ClientService.get_n8n_api_key(db, client_id)
            if not api_key or not client.n8n_api_url:
                print("❌ Missing API key or URL")
                return
            
            print(f"📋 Client: {client.name}")
            print(f"🔗 URL: {client.n8n_api_url}")
            
            # Test workflows
            print("\n📊 Fetching ALL workflows...")
            workflows = await MetricsService._fetch_workflows(client.n8n_api_url, api_key)
            print(f"✅ Total workflows found: {len(workflows)}")
            
            # Show active vs inactive
            active_count = len([w for w in workflows if w.get('active', False)])
            inactive_count = len(workflows) - active_count
            print(f"   🟢 Active: {active_count}")
            print(f"   🔴 Inactive: {inactive_count}")
            
            # Show first few workflow names
            print("\n📝 First 10 workflows:")
            for i, workflow in enumerate(workflows[:10]):
                name = workflow.get('name', 'Unnamed')
                active = "🟢" if workflow.get('active', False) else "🔴"
                print(f"   {i+1}. {active} {name}")
            
            # Test executions
            print(f"\n⚡ Fetching recent executions...")
            executions = await MetricsService._fetch_executions(client.n8n_api_url, api_key)
            print(f"✅ Total executions found: {len(executions)}")
            
            # Show execution stats
            if executions:
                finished_count = len([e for e in executions if e.get('finished', False)])
                running_count = len([e for e in executions if not e.get('finished', False)])
                print(f"   ✅ Finished: {finished_count}")
                print(f"   🔄 Running/Other: {running_count}")
                
                # Show most recent executions
                print("\n🕐 Most recent executions:")
                for i, execution in enumerate(executions[:5]):
                    workflow_id = execution.get('workflowId', 'Unknown')
                    status = execution.get('status', 'unknown')
                    started = execution.get('startedAt', 'Unknown')[:19]  # Trim timestamp
                    print(f"   {i+1}. Workflow {workflow_id} - {status} - {started}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await db.close()
            break

if __name__ == "__main__":
    client_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    asyncio.run(test_unlimited_fetch(client_id))