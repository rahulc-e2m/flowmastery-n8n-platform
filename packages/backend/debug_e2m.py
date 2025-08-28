#!/usr/bin/env python3
"""Debug script for E2M Solutions metrics"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func, and_
from app.config.settings import settings
from app.models import Client, Workflow, WorkflowExecution, ExecutionStatus

async def debug_e2m():
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
                
            print(f"=== E2M Solutions Debug (Client ID: {e2m_client.id}) ===")
            
            # Get all executions for E2M
            all_exec_stmt = select(func.count(WorkflowExecution.id)).where(
                WorkflowExecution.client_id == e2m_client.id
            )
            all_exec_count = (await db.execute(all_exec_stmt)).scalar_one()
            print(f"Total executions (all): {all_exec_count}")
            
            # Get production executions
            prod_exec_stmt = select(func.count(WorkflowExecution.id)).where(
                and_(
                    WorkflowExecution.client_id == e2m_client.id,
                    WorkflowExecution.is_production == True
                )
            )
            prod_exec_count = (await db.execute(prod_exec_stmt)).scalar_one()
            print(f"Production executions: {prod_exec_count}")
            
            # Get successful production executions
            success_stmt = select(func.count(WorkflowExecution.id)).where(
                and_(
                    WorkflowExecution.client_id == e2m_client.id,
                    WorkflowExecution.is_production == True,
                    WorkflowExecution.status == ExecutionStatus.SUCCESS
                )
            )
            success_count = (await db.execute(success_stmt)).scalar_one()
            print(f"Successful executions: {success_count}")
            
            # Get failed production executions
            failed_stmt = select(func.count(WorkflowExecution.id)).where(
                and_(
                    WorkflowExecution.client_id == e2m_client.id,
                    WorkflowExecution.is_production == True,
                    WorkflowExecution.status == ExecutionStatus.ERROR
                )
            )
            failed_count = (await db.execute(failed_stmt)).scalar_one()
            print(f"Failed executions: {failed_count}")
            
            # Calculate actual success rate
            if prod_exec_count > 0:
                actual_success_rate = (success_count / prod_exec_count) * 100
                print(f"Calculated success rate: {actual_success_rate:.1f}%")
            
            # Get workflows and their time saved settings
            workflows_stmt = select(Workflow.id, Workflow.name, Workflow.time_saved_per_execution_minutes).where(
                Workflow.client_id == e2m_client.id
            )
            workflows_result = await db.execute(workflows_stmt)
            workflows = workflows_result.all()
            
            print(f"\nWorkflows ({len(workflows)}):")
            total_minutes_saved = 0
            for wf_id, wf_name, minutes in workflows:
                # Count successful executions for this workflow
                wf_success_stmt = select(func.count(WorkflowExecution.id)).where(
                    and_(
                        WorkflowExecution.workflow_id == wf_id,
                        WorkflowExecution.is_production == True,
                        WorkflowExecution.status == ExecutionStatus.SUCCESS
                    )
                )
                wf_success_count = (await db.execute(wf_success_stmt)).scalar_one()
                
                wf_minutes_saved = wf_success_count * (minutes or 30)
                total_minutes_saved += wf_minutes_saved
                
                print(f"  {wf_name}: {wf_success_count} successes × {minutes or 30} min = {wf_minutes_saved} min")
            
            total_hours_saved = total_minutes_saved / 60
            print(f"\nTotal minutes saved: {total_minutes_saved}")
            print(f"Total hours saved: {total_hours_saved:.1f}h")
            
            # Check if there are any non-production executions that might be affecting the count
            non_prod_stmt = select(func.count(WorkflowExecution.id)).where(
                and_(
                    WorkflowExecution.client_id == e2m_client.id,
                    WorkflowExecution.is_production == False
                )
            )
            non_prod_count = (await db.execute(non_prod_stmt)).scalar_one()
            print(f"Non-production executions: {non_prod_count}")
            
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_e2m())