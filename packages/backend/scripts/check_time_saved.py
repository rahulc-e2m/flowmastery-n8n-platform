#!/usr/bin/env python
"""Diagnostic script to check time saved calculations"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.models import (
    Client, 
    Workflow, 
    WorkflowExecution, 
    MetricsAggregation, 
    ExecutionStatus,
    AggregationPeriod
)


async def check_time_saved_data():
    """Check time saved data integrity"""
    
    async for db in get_db():
        try:
            print("=" * 80)
            print("TIME SAVED DIAGNOSTIC REPORT")
            print("=" * 80)
            
            # 1. Check workflow configurations
            print("\n1. WORKFLOW TIME SAVED CONFIGURATIONS:")
            print("-" * 40)
            
            workflows = await db.execute(
                select(Workflow.client_id, Workflow.name, Workflow.time_saved_per_execution_minutes)
                .order_by(Workflow.client_id)
            )
            workflow_data = workflows.all()
            
            for client_id, name, minutes in workflow_data[:10]:  # Show first 10
                print(f"Client {client_id} - {name}: {minutes or 30} minutes per execution")
            
            # 2. Check successful executions count
            print("\n2. SUCCESSFUL EXECUTIONS BY CLIENT:")
            print("-" * 40)
            
            success_counts = await db.execute(
                select(
                    WorkflowExecution.client_id,
                    func.count(WorkflowExecution.id).label('total_success')
                ).where(
                    and_(
                        WorkflowExecution.status == ExecutionStatus.SUCCESS,
                        WorkflowExecution.is_production == True
                    )
                ).group_by(WorkflowExecution.client_id)
            )
            
            for client_id, count in success_counts.all():
                print(f"Client {client_id}: {count} successful executions")
            
            # 3. Check recent aggregations
            print("\n3. RECENT AGGREGATIONS (LAST 5):")
            print("-" * 40)
            
            recent_aggs = await db.execute(
                select(MetricsAggregation)
                .where(MetricsAggregation.workflow_id.is_(None))  # Client-wide only
                .order_by(desc(MetricsAggregation.computed_at))
                .limit(5)
            )
            
            for agg in recent_aggs.scalars().all():
                print(f"Client {agg.client_id} - Date: {agg.period_start}")
                print(f"  Success: {agg.successful_executions}, Hours saved: {agg.time_saved_hours}")
                print(f"  Total: {agg.total_executions}, Success rate: {agg.success_rate:.1f}%")
            
            # 4. Calculate time saved manually for verification
            print("\n4. MANUAL TIME SAVED CALCULATION (PER CLIENT):")
            print("-" * 40)
            
            clients = await db.execute(select(Client))
            
            for client in clients.scalars().all():
                # Get all successful executions
                success_execs = await db.execute(
                    select(
                        WorkflowExecution.workflow_id,
                        func.count(WorkflowExecution.id).label('count')
                    ).where(
                        and_(
                            WorkflowExecution.client_id == client.id,
                            WorkflowExecution.status == ExecutionStatus.SUCCESS,
                            WorkflowExecution.is_production == True
                        )
                    ).group_by(WorkflowExecution.workflow_id)
                )
                
                # Get workflow time saved minutes
                workflow_minutes = await db.execute(
                    select(Workflow.id, Workflow.time_saved_per_execution_minutes)
                    .where(Workflow.client_id == client.id)
                )
                minutes_map = {wid: (mins or 30) for wid, mins in workflow_minutes.all()}
                
                # Calculate total
                total_minutes = 0
                exec_by_workflow = success_execs.all()
                
                for workflow_id, count in exec_by_workflow:
                    minutes = minutes_map.get(workflow_id, 30)
                    total_minutes += count * minutes
                
                total_hours = round(total_minutes / 60, 1)
                
                print(f"Client {client.id} ({client.name}):")
                print(f"  Total successful executions: {sum(count for _, count in exec_by_workflow)}")
                print(f"  Total time saved: {total_hours} hours ({total_minutes} minutes)")
            
            # 5. Check for data inconsistencies
            print("\n5. DATA CONSISTENCY CHECK:")
            print("-" * 40)
            
            # Check if we have executions without workflows
            orphan_execs = await db.execute(
                select(func.count(WorkflowExecution.id))
                .outerjoin(Workflow, WorkflowExecution.workflow_id == Workflow.id)
                .where(Workflow.id.is_(None))
            )
            orphan_count = orphan_execs.scalar()
            
            if orphan_count:
                print(f"⚠️ WARNING: Found {orphan_count} executions without valid workflows!")
            else:
                print("✅ All executions have valid workflows")
            
            # Check aggregations vs raw data for today
            today = datetime.utcnow().date()
            
            for client in clients.scalars().all():
                # Get today's aggregation
                today_agg = await db.execute(
                    select(MetricsAggregation)
                    .where(
                        and_(
                            MetricsAggregation.client_id == client.id,
                            MetricsAggregation.period_start == today,
                            MetricsAggregation.period_type == AggregationPeriod.DAILY,
                            MetricsAggregation.workflow_id.is_(None)
                        )
                    )
                )
                agg = today_agg.scalar_one_or_none()
                
                if agg:
                    # Count actual executions for today
                    actual = await db.execute(
                        select(func.count(WorkflowExecution.id))
                        .where(
                            and_(
                                WorkflowExecution.client_id == client.id,
                                WorkflowExecution.is_production == True,
                                WorkflowExecution.started_at >= datetime.combine(today, datetime.min.time()),
                                WorkflowExecution.started_at < datetime.combine(today + timedelta(days=1), datetime.min.time())
                            )
                        )
                    )
                    actual_count = actual.scalar()
                    
                    if actual_count != agg.total_executions:
                        print(f"⚠️ Client {client.id}: Aggregation shows {agg.total_executions}, actual is {actual_count}")
            
            print("\n" + "=" * 80)
            print("END OF DIAGNOSTIC REPORT")
            print("=" * 80)
            
        finally:
            await db.close()


if __name__ == "__main__":
    asyncio.run(check_time_saved_data())
