#!/usr/bin/env python3
"""Test caching performance"""

import asyncio
import time
import sys
sys.path.append('.')

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.metrics_service import MetricsService

async def test_caching_performance(client_id: int = 1):
    """Test caching performance"""
    print(f"🧪 Testing caching performance for client {client_id}")
    
    async for db in get_db():
        try:
            # First call (no cache) - should be slow
            print("\n🐌 First call (no cache)...")
            start_time = time.time()
            metrics1 = await MetricsService.get_client_metrics(db, client_id, use_cache=False)
            first_call_time = time.time() - start_time
            print(f"   ⏱️  Time: {first_call_time:.2f} seconds")
            print(f"   📊 Workflows: {metrics1.total_workflows}")
            print(f"   ⚡ Executions: {metrics1.total_executions}")
            
            # Second call (with cache) - should be fast
            print("\n🚀 Second call (with cache)...")
            start_time = time.time()
            metrics2 = await MetricsService.get_client_metrics(db, client_id, use_cache=True)
            second_call_time = time.time() - start_time
            print(f"   ⏱️  Time: {second_call_time:.2f} seconds")
            print(f"   📊 Workflows: {metrics2.total_workflows}")
            print(f"   ⚡ Executions: {metrics2.total_executions}")
            
            # Performance improvement
            if first_call_time > 0:
                improvement = (first_call_time - second_call_time) / first_call_time * 100
                speedup = first_call_time / second_call_time if second_call_time > 0 else float('inf')
                print(f"\n🎯 Performance Results:")
                print(f"   📈 Speed improvement: {improvement:.1f}%")
                print(f"   🚀 Speedup: {speedup:.1f}x faster")
                
                if improvement > 80:
                    print("   ✅ Excellent caching performance!")
                elif improvement > 50:
                    print("   👍 Good caching performance!")
                else:
                    print("   ⚠️  Caching might need optimization")
            
            # Third call (cache hit) - should be even faster
            print("\n⚡ Third call (cache hit)...")
            start_time = time.time()
            metrics3 = await MetricsService.get_client_metrics(db, client_id, use_cache=True)
            third_call_time = time.time() - start_time
            print(f"   ⏱️  Time: {third_call_time:.2f} seconds")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await db.close()
            break

if __name__ == "__main__":
    client_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    asyncio.run(test_caching_performance(client_id))