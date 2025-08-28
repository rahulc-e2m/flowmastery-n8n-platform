#!/usr/bin/env python3
"""Test script to check current metrics calculations"""

import asyncio
import sys
import os

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.services.enhanced_metrics_service import enhanced_metrics_service
from app.config.settings import settings

async def test_metrics():
    try:
        engine = create_async_engine(settings.DATABASE_URL)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as db:
            # Test admin metrics
            admin_metrics = await enhanced_metrics_service.get_admin_metrics(db)
            print('=== Admin Metrics ===')
            print(f'Total Clients: {admin_metrics.total_clients}')
            print(f'Total Workflows: {admin_metrics.total_workflows}')
            print(f'Total Executions: {admin_metrics.total_executions}')
            print(f'Success Rate: {admin_metrics.overall_success_rate}%')
            print(f'Time Saved: {admin_metrics.total_time_saved_hours}h')
            print()
            
            # Test client metrics for each client
            for client in admin_metrics.clients:
                print(f'=== {client.client_name} Metrics ===')
                print(f'Total Workflows: {client.total_workflows}')
                print(f'Active Workflows: {client.active_workflows}')
                print(f'Total Executions: {client.total_executions}')
                print(f'Successful: {client.successful_executions}')
                print(f'Failed: {client.failed_executions}')
                print(f'Success Rate: {client.success_rate}%')
                print(f'Time Saved: {client.time_saved_hours}h')
                print()
                
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_metrics())