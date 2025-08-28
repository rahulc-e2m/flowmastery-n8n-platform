#!/usr/bin/env python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.sync_connection import get_sync_db_session
from sqlalchemy import text

with get_sync_db_session() as db:
    db.execute(text("DROP TABLE IF EXISTS sync_states CASCADE"))
    db.commit()
    print("Table sync_states dropped successfully")
