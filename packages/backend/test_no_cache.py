#!/usr/bin/env python3
"""Test metrics without cache"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.services.enhanced_metrics_service import enhanced_metrics_service
from app.config.settings import settings

async def test_no_cache():
    try:
        engine = create_async_engine(settings.DATABASE_URL)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as db:
            # Test E2M Solutions metrics WITHOUT cache
            print("=== E2M Solutions Metrics (NO CACHE) ===")
            client_metrics = await enhanced_metrics_service.get_client_metrics(db, 1, use_cache=False)
            print(f'Total Workflows: {client_metrics.total_workflows}')
            print(f'Active Workflows: {client_metrics.active_workflows}')
            print(f'Total Executions: {client_metrics.total_executions}')
            print(f'Successful: {client_metrics.successful_executions}')
            print(f'Failed: {client_metrics.failed_executions}')
            print(f'Success Rate: {client_metrics.success_rate}%')
            print(f'Time Saved: {client_metrics.time_saved_hours}h')
            print()
            
            # Test admin metrics WITHOUT cache
            print("=== Admin Metrics (NO CACHE) ===")
            admin_metrics = await enhanced_metrics_service.get_admin_metrics(db)
            print(f'Total Clients: {admin_metrics.total_clients}')
            print(f'Total Workflows: {admin_metrics.total_workflows}')
            print(f'Total Executions: {admin_metrics.total_executions}')
            print(f'Success Rate: {admin_metrics.overall_success_rate}%')
            print(f'Time Saved: {admin_metrics.total_time_saved_hours}h')
                
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_no_cache())