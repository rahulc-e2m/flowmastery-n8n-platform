"""Celery application configuration for FlowMastery"""

import os
from celery import Celery
from celery.schedules import crontab
from kombu import Exchange, Queue

from app.config import settings

# Create Celery instance
celery_app = Celery(
    "flowmastery",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['app.tasks.metrics_tasks', 'app.tasks.aggregation_tasks']
)

# Celery configuration
celery_app.conf.update(
    # Task serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task execution
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    task_acks_late=True,
    
    # Result backend - Fixed configuration for Redis
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        'visibility_timeout': 3600,
        'retry_policy': {
            'timeout': 5.0
        }
    },
    result_backend_db=0,
    result_persistent=True,
    task_ignore_result=False,
    
    # Task routing and queues
    task_default_queue='default',
    task_default_exchange='default',
    task_default_exchange_type='direct',
    task_default_routing_key='default',
    
    task_routes={
        'app.tasks.metrics_tasks.sync_client_metrics': {'queue': 'metrics'},
        'app.tasks.metrics_tasks.sync_all_clients_metrics': {'queue': 'metrics'},
        'app.tasks.aggregation_tasks.compute_daily_aggregations': {'queue': 'aggregation'},
        'app.tasks.aggregation_tasks.compute_weekly_aggregations': {'queue': 'aggregation'},
        'app.tasks.aggregation_tasks.compute_monthly_aggregations': {'queue': 'aggregation'},
        'app.tasks.aggregation_tasks.cleanup_old_data': {'queue': 'maintenance'},
    },
    
    task_queues=(
        Queue('default', Exchange('default'), routing_key='default'),
        Queue('metrics', Exchange('metrics'), routing_key='metrics'),
        Queue('aggregation', Exchange('aggregation'), routing_key='aggregation'),
        Queue('maintenance', Exchange('maintenance'), routing_key='maintenance'),
    ),
    
    # Beat schedule for periodic tasks
    beat_schedule={
        'sync-metrics-every-15-minutes': {
            'task': 'app.tasks.metrics_tasks.sync_all_clients_metrics',
            'schedule': 15 * 60,  # 15 minutes in seconds
            'options': {'queue': 'metrics', 'expires': 10 * 60}  # Expire if not run within 10 min
        },
        'daily-aggregation': {
            'task': 'app.tasks.aggregation_tasks.compute_daily_aggregations',
            'schedule': crontab(hour=2, minute=0),  # Daily at 2:00 AM
            'options': {'queue': 'aggregation'}
        },
        'weekly-aggregation': {
            'task': 'app.tasks.aggregation_tasks.compute_weekly_aggregations',
            'schedule': crontab(day_of_week=0, hour=3, minute=0),  # Sunday at 3:00 AM
            'options': {'queue': 'aggregation'}
        },
        'monthly-aggregation': {
            'task': 'app.tasks.aggregation_tasks.compute_monthly_aggregations',
            'schedule': crontab(day_of_month=1, hour=4, minute=0),  # 1st of month at 4:00 AM
            'options': {'queue': 'aggregation'}
        },
        'cleanup-old-data': {
            'task': 'app.tasks.aggregation_tasks.cleanup_old_data',
            'schedule': crontab(hour=1, minute=0),  # Daily at 1:00 AM
            'options': {'queue': 'maintenance'}
        },
    },
    
    # Worker configuration
    worker_hijack_root_logger=False,
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)