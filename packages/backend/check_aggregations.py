#!/usr/bin/env python3
"""Check aggregations vs raw data"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func, and_, desc
from app.config.settings import settings
from app.models import Client, MetricsAggregation, AggregationPeriod

async def check_aggregations():
    try:
        engine = create_async_engine(settings.DATABASE_URL)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as db:
            # Find E2M Solutions client
            client_stmt = select(Client).where(Client.name.ilike('%E2M%'))
            client_result = await db.execute(client_stmt)
            e2m_client = client_result.scalar_one_or_none()
            
            if not e2m_client:
                print("E2M Solutions client not found")
                return
                
            print(f"=== E2M Solutions Aggregations (Client ID: {e2m_client.id}) ===")
            
            # Get recent daily aggregations for E2M
            daily_agg_stmt = select(MetricsAggregation).where(
                and_(
                    MetricsAggregation.client_id == e2m_client.id,
                    MetricsAggregation.workflow_id.is_(None),  # Client-wide aggregation
                    MetricsAggregation.period_type == AggregationPeriod.DAILY
                )
            ).order_by(desc(MetricsAggregation.period_start)).limit(5)
            
            daily_result = await db.execute(daily_agg_stmt)
            daily_aggregations = daily_result.scalars().all()
            
            print("Recent Daily Aggregations:")
            for agg in daily_aggregations:
                print(f"  {agg.period_start}: {agg.total_executions} executions, {agg.successful_executions} successful, {agg.success_rate:.1f}% success rate, {agg.time_saved_hours:.1f}h saved")
            
            # Check if there are any recent aggregations that might be used instead of all-time data
            if daily_aggregations:
                latest_agg = daily_aggregations[0]
                print(f"\nLatest aggregation shows: {latest_agg.total_executions} executions")
                print("This might be what's being displayed instead of all-time totals")
            
            # Check admin-level aggregations
            print("\n=== Admin Level Aggregations ===")
            admin_agg_stmt = select(MetricsAggregation).where(
                and_(
                    MetricsAggregation.client_id.is_(None),  # Admin-wide aggregation
                    MetricsAggregation.workflow_id.is_(None),
                    MetricsAggregation.period_type == AggregationPeriod.DAILY
                )
            ).order_by(desc(MetricsAggregation.period_start)).limit(3)
            
            admin_result = await db.execute(admin_agg_stmt)
            admin_aggregations = admin_result.scalars().all()
            
            for agg in admin_aggregations:
                print(f"  {agg.period_start}: {agg.total_executions} total executions, {agg.successful_executions} successful, {agg.success_rate:.1f}% success rate")
                
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_aggregations())