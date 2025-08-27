#!/usr/bin/env python3
"""
Debug script for dashboard refresh issues
Run this to diagnose problems with dashboard data refresh
"""

import asyncio
import sys
import os
from datetime import datetime, timezone

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.database.connection import get_async_db_session
from app.services.cache.redis import redis_client
from app.services.enhanced_metrics_service import enhanced_metrics_service
from app.models import Client, WorkflowExecution, MetricsAggregation
from sqlalchemy import select, func


async def check_database_data():
    """Check database for recent data"""
    print("🔍 Checking database data...")
    
    async with get_async_db_session() as db:
        # Check clients
        clients_stmt = select(Client)
        clients_result = await db.execute(clients_stmt)
        clients = clients_result.scalars().all()
        
        print(f"📊 Found {len(clients)} clients")
        
        for client in clients:
            print(f"\n  Client: {client.name} (ID: {client.id})")
            
            # Check last sync
            last_sync_stmt = select(func.max(WorkflowExecution.last_synced_at)).where(
                WorkflowExecution.client_id == client.id
            )
            last_sync_result = await db.execute(last_sync_stmt)
            last_sync = last_sync_result.scalar_one_or_none()
            
            if last_sync:
                age = datetime.now(timezone.utc) - last_sync.replace(tzinfo=timezone.utc)
                print(f"    Last sync: {last_sync} ({age.total_seconds()/60:.1f} minutes ago)")
            else:
                print("    Last sync: Never")
            
            # Check executions count
            exec_count_stmt = select(func.count(WorkflowExecution.id)).where(
                WorkflowExecution.client_id == client.id,
                WorkflowExecution.is_production == True
            )
            exec_count_result = await db.execute(exec_count_stmt)
            exec_count = exec_count_result.scalar_one_or_none() or 0
            print(f"    Production executions: {exec_count}")
            
            # Check aggregations
            agg_stmt = select(func.max(MetricsAggregation.computed_at)).where(
                MetricsAggregation.client_id == client.id
            )
            agg_result = await db.execute(agg_stmt)
            last_agg = agg_result.scalar_one_or_none()
            
            if last_agg:
                age = datetime.now(timezone.utc) - last_agg.replace(tzinfo=timezone.utc)
                print(f"    Last aggregation: {last_agg} ({age.total_seconds()/60:.1f} minutes ago)")
            else:
                print("    Last aggregation: Never")


async def check_cache_status():
    """Check Redis cache status"""
    print("\n🗄️  Checking cache status...")
    
    # Test Redis connection
    if await redis_client.ping():
        print("  ✅ Redis connection: OK")
    else:
        print("  ❌ Redis connection: FAILED")
        return
    
    # Check cache keys
    cache_patterns = [
        "enhanced_client_metrics:*",
        "client_metrics:*", 
        "admin_metrics:*"
    ]
    
    for pattern in cache_patterns:
        keys = await redis_client.client.keys(pattern)
        print(f"  Cache pattern '{pattern}': {len(keys)} keys")
        
        for key in keys[:3]:  # Show first 3 keys
            key_str = key.decode('utf-8') if isinstance(key, bytes) else key
            exists = await redis_client.exists(key_str)
            print(f"    - {key_str}: {'exists' if exists else 'missing'}")


async def test_metrics_service():
    """Test the metrics service directly"""
    print("\n🧪 Testing metrics service...")
    
    async with get_async_db_session() as db:
        try:
            # Test admin metrics
            admin_metrics = await enhanced_metrics_service.get_admin_metrics(db)
            print(f"  ✅ Admin metrics: {admin_metrics.total_clients} clients, {admin_metrics.total_executions} executions")
            
            if admin_metrics.last_updated:
                age = datetime.now(timezone.utc) - admin_metrics.last_updated.replace(tzinfo=timezone.utc)
                print(f"    Last updated: {admin_metrics.last_updated} ({age.total_seconds()/60:.1f} minutes ago)")
            
            # Test individual client metrics
            for client in admin_metrics.clients[:2]:  # Test first 2 clients
                try:
                    client_metrics = await enhanced_metrics_service.get_client_metrics(db, client.client_id)
                    print(f"  ✅ Client {client.client_name}: {client_metrics.total_executions} executions")
                except Exception as e:
                    print(f"  ❌ Client {client.client_name}: {e}")
                    
        except Exception as e:
            print(f"  ❌ Metrics service error: {e}")


async def check_celery_status():
    """Check Celery worker status"""
    print("\n⚙️  Checking Celery status...")
    
    try:
        from app.core.celery_app import celery_app
        
        # Check if we can import celery
        print("  ✅ Celery app imported successfully")
        
        # Try to get worker stats
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        
        if stats:
            print(f"  ✅ Active workers: {len(stats)}")
            for worker_name, worker_stats in stats.items():
                print(f"    - {worker_name}: {worker_stats.get('total', 'unknown')} tasks processed")
        else:
            print("  ⚠️  No active workers found")
        
        # Check active tasks
        active = inspect.active()
        if active:
            total_active = sum(len(tasks) for tasks in active.values())
            print(f"  📋 Active tasks: {total_active}")
        else:
            print("  📋 No active tasks")
            
    except Exception as e:
        print(f"  ❌ Celery check failed: {e}")


async def main():
    """Main diagnostic function"""
    print("🚀 Dashboard Refresh Diagnostic Tool")
    print("=" * 50)
    
    try:
        await check_database_data()
        await check_cache_status()
        await test_metrics_service()
        await check_celery_status()
        
        print("\n" + "=" * 50)
        print("✅ Diagnostic complete!")
        print("\n💡 Recommendations:")
        print("   - If cache is empty, run: POST /metrics/admin/refresh-cache")
        print("   - If data is stale, run: POST /metrics/admin/quick-sync")
        print("   - If Celery workers are down, restart them")
        print("   - Check logs for specific error messages")
        
    except Exception as e:
        print(f"\n❌ Diagnostic failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await redis_client.close()


if __name__ == "__main__":
    asyncio.run(main())