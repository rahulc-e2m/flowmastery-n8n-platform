#!/usr/bin/env python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.sync_connection import get_sync_db_session
from app.models import Workflow
from sqlalchemy import select

with get_sync_db_session() as db:
    # Get workflows with custom time saved minutes
    result = db.execute(
        select(
            Workflow.client_id, 
            Workflow.name, 
            Workflow.time_saved_per_execution_minutes
        ).where(
            Workflow.time_saved_per_execution_minutes.isnot(None)
        ).order_by(Workflow.client_id)
    )
    
    print("Workflows with custom time saved minutes:")
    print("-" * 50)
    for client_id, name, minutes in result.all():
        print(f"Client {client_id}: {name} = {minutes} minutes")
    
    print("\n\nAll workflows (showing first 20):")
    print("-" * 50)
    all_wf = db.execute(
        select(
            Workflow.client_id, 
            Workflow.name, 
            Workflow.time_saved_per_execution_minutes
        ).limit(20)
    )
    
    for client_id, name, minutes in all_wf.all():
        print(f"Client {client_id}: {name} = {minutes or 30} minutes (default: 30)")
