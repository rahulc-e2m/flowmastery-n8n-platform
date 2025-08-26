#!/usr/bin/env python3
"""
Celery worker startup script for FlowMastery metrics system
"""

import os
import sys
from celery import Celery

# Add app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.celery_app import celery_app

if __name__ == '__main__':
    print("🚀 Starting FlowMastery Celery Worker")
    print("📊 Queues: metrics, aggregation, maintenance, default")
    print("⏱️  Beat schedule: metrics sync every 15 minutes")
    print("🔧 Use 'celery -A app.core.celery_app worker --loglevel=info' to start")
    
    # This is just for reference - actual worker should be started with celery command
    celery_app.start()