#!/usr/bin/env python3
"""Detailed time saved analysis"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func, and_
from app.config.settings import settings
from app.models import Client, Workflow, WorkflowExecution, ExecutionStatus

async def detailed_time_analysis():
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
                
            print(f"=== E2M Solutions Time Saved Analysis (Client ID: {e2m_client.id}) ===")
            
            # Get workflows with non-default time saved settings
            workflows_stmt = select(
                Workflow.id, 
                Workflow.name, 
                Workflow.time_saved_per_execution_minutes
            ).where(
                and_(
                    Workflow.client_id == e2m_client.id,
                    Workflow.time_saved_per_execution_minutes != 30  # Non-default values
                )
            )
            workflows_result = await db.execute(workflows_stmt)
            non_default_workflows = workflows_result.all()
            
            print(f"Workflows with non-default time saved settings:")
            total_custom_minutes = 0
            for wf_id, wf_name, minutes in non_default_workflows:
                # Count successful executions for this workflow
                wf_success_stmt = select(func.count(WorkflowExecution.id)).where(
                    and_(
                        WorkflowExecution.workflow_id == wf_id,
                        WorkflowExecution.is_production == True,
                        WorkflowExecution.status == ExecutionStatus.SUCCESS
                    )
                )
                wf_success_count = (await db.execute(wf_success_stmt)).scalar_one()
                
                wf_minutes_saved = wf_success_count * minutes
                total_custom_minutes += wf_minutes_saved
                
                if wf_success_count > 0:  # Only show workflows with successful executions
                    print(f"  {wf_name}: {wf_success_count} successes × {minutes} min = {wf_minutes_saved} min")
            
            # Get workflows with default time saved (30 min)
            default_workflows_stmt = select(
                Workflow.id, 
                Workflow.name
            ).where(
                and_(
                    Workflow.client_id == e2m_client.id,
                    Workflow.time_saved_per_execution_minutes == 30
                )
            )
            default_workflows_result = await db.execute(default_workflows_stmt)
            default_workflows = default_workflows_result.all()
            
            print(f"\nWorkflows with default time saved (30 min) that have successful executions:")
            total_default_minutes = 0
            for wf_id, wf_name in default_workflows:
                # Count successful executions for this workflow
                wf_success_stmt = select(func.count(WorkflowExecution.id)).where(
                    and_(
                        WorkflowExecution.workflow_id == wf_id,
                        WorkflowExecution.is_production == True,
                        WorkflowExecution.status == ExecutionStatus.SUCCESS
                    )
                )
                wf_success_count = (await db.execute(wf_success_stmt)).scalar_one()
                
                if wf_success_count > 0:  # Only show workflows with successful executions
                    wf_minutes_saved = wf_success_count * 30
                    total_default_minutes += wf_minutes_saved
                    print(f"  {wf_name}: {wf_success_count} successes × 30 min = {wf_minutes_saved} min")
            
            total_minutes = total_custom_minutes + total_default_minutes
            total_hours = total_minutes / 60
            
            print(f"\nSummary:")
            print(f"Custom time saved: {total_custom_minutes} minutes")
            print(f"Default time saved: {total_default_minutes} minutes")
            print(f"Total minutes saved: {total_minutes}")
            print(f"Total hours saved: {total_hours:.1f}h")
            
            # Expected values from your analysis
            expected_minutes = 5130
            expected_hours = 85.5
            
            print(f"\nComparison:")
            print(f"Expected: {expected_minutes} minutes ({expected_hours}h)")
            print(f"Actual: {total_minutes} minutes ({total_hours:.1f}h)")
            print(f"Difference: {total_minutes - expected_minutes} minutes ({total_hours - expected_hours:.1f}h)")
                
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(detailed_time_analysis())