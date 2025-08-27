"""Celery tasks for metrics collection and synchronization"""

import logging
from typing import Dict, Any, List
from celery import current_task
from celery.exceptions import Retry

from app.core.celery_app import celery_app
from app.database.sync_connection import get_sync_db_session
from app.services.sync_metrics_collector import sync_metrics_collector
from app.models import Client

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    name='app.tasks.metrics_tasks.sync_client_metrics',
    acks_late=True,
    reject_on_worker_lost=True
)
def sync_client_metrics(self, client_id: int) -> Dict[str, Any]:
    """
    Sync metrics for a specific client
    
    Args:
        client_id: ID of the client to sync
        
    Returns:
        Dict with sync results
    """
    task_id = self.request.id
    logger.info(f"Starting metrics sync for client {client_id} (task: {task_id})")
    
    try:
        # Use synchronous database session
        with get_sync_db_session() as db:
            result = sync_metrics_collector.sync_client_data(db, client_id)
        
        logger.info(f"Completed metrics sync for client {client_id}: {result}")
        
        # Invalidate cache for this client after successful sync
        try:
            from app.services.cache.redis import redis_client
            import asyncio
            
            # Clear client-specific cache
            cache_keys = [
                f"enhanced_client_metrics:{client_id}",
                f"client_metrics:{client_id}",
                f"client_workflows:{client_id}"
            ]
            
            # Run cache clearing in async context
            async def clear_cache():
                for key in cache_keys:
                    await redis_client.delete(key)
                # Also clear admin metrics cache since it includes this client
                await redis_client.clear_pattern("admin_metrics:*")
                await redis_client.clear_pattern("enhanced_client_metrics:*")
            
            # Execute cache clearing
            try:
                loop = asyncio.get_event_loop()
                loop.run_until_complete(clear_cache())
            except RuntimeError:
                # If no event loop, create one
                asyncio.run(clear_cache())
                
        except Exception as cache_error:
            logger.warning(f"Failed to clear cache after sync: {cache_error}")
        
        return {
            'status': 'success',
            'client_id': client_id,
            'task_id': task_id,
            'result': result
        }
        
    except Exception as exc:
        logger.error(f"Failed to sync client {client_id}: {exc}")
        
        # Update task state for monitoring
        self.update_state(
            state='FAILURE',
            meta={
                'client_id': client_id,
                'error': str(exc),
                'retry_count': self.request.retries
            }
        )
        
        # Re-raise to trigger retry mechanism
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 2, 'countdown': 120},
    name='app.tasks.metrics_tasks.sync_all_clients_metrics',
    acks_late=True,
    reject_on_worker_lost=True
)
def sync_all_clients_metrics(self) -> Dict[str, Any]:
    """
    Sync metrics for all clients with n8n configuration
    
    Returns:
        Dict with overall sync results
    """
    task_id = self.request.id
    logger.info(f"Starting metrics sync for all clients (task: {task_id})")
    
    try:
        # Use synchronous database session
        with get_sync_db_session() as db:
            result = sync_metrics_collector.sync_all_clients(db)
        
        logger.info(f"Completed metrics sync for all clients: {result}")
        
        # Schedule individual client syncs for failed clients if any
        if result.get('errors'):
            logger.warning(f"Scheduling retry for failed clients: {len(result['errors'])} errors")
        
        # Clear all metrics cache after successful sync
        try:
            from app.services.cache.redis import redis_client
            import asyncio
            
            async def clear_all_cache():
                # Clear all metrics-related cache
                await redis_client.clear_pattern("enhanced_client_metrics:*")
                await redis_client.clear_pattern("client_metrics:*")
                await redis_client.clear_pattern("client_workflows:*")
                await redis_client.clear_pattern("admin_metrics:*")
                logger.info("Cleared all metrics cache after sync")
            
            # Execute cache clearing
            try:
                loop = asyncio.get_event_loop()
                loop.run_until_complete(clear_all_cache())
            except RuntimeError:
                asyncio.run(clear_all_cache())
                
        except Exception as cache_error:
            logger.warning(f"Failed to clear cache after all clients sync: {cache_error}")
            
        return {
            'status': 'success',
            'task_id': task_id,
            'result': result
        }
        
    except Exception as exc:
        logger.error(f"Failed to sync all clients: {exc}")
        
        self.update_state(
            state='FAILURE',
            meta={
                'error': str(exc),
                'retry_count': self.request.retries
            }
        )
        
        raise self.retry(exc=exc, countdown=120 * (2 ** self.request.retries))


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 1, 'countdown': 300},
    name='app.tasks.metrics_tasks.batch_sync_clients'
)
def batch_sync_clients(self, client_ids: List[int]) -> Dict[str, Any]:
    """
    Sync metrics for a batch of specific clients
    
    Args:
        client_ids: List of client IDs to sync
        
    Returns:
        Dict with batch sync results
    """
    task_id = self.request.id
    logger.info(f"Starting batch metrics sync for {len(client_ids)} clients (task: {task_id})")
    
    results = {
        'successful': [],
        'failed': [],
        'task_id': task_id
    }
    
    for client_id in client_ids:
        try:
            # Use the single client sync task
            client_result = sync_client_metrics.apply_async(
                args=[client_id],
                queue='metrics',
                expires=600  # 10 minutes
            )
            
            # Wait for result with timeout
            result = client_result.get(timeout=300)  # 5 minutes
            results['successful'].append({
                'client_id': client_id,
                'result': result
            })
            
        except Exception as exc:
            logger.error(f"Batch sync failed for client {client_id}: {exc}")
            results['failed'].append({
                'client_id': client_id,
                'error': str(exc)
            })
    
    logger.info(f"Batch sync completed: {len(results['successful'])} successful, {len(results['failed'])} failed")
    return results


@celery_app.task(
    bind=True,
    name='app.tasks.metrics_tasks.health_check'
)
def health_check(self) -> Dict[str, Any]:
    """
    Health check task for monitoring Celery worker status
    
    Returns:
        Dict with health status
    """
    task_id = self.request.id
    
    try:
        # Use synchronous database session for health check
        with get_sync_db_session() as db:
            from sqlalchemy import text
            result = db.execute(text("SELECT 1"))
            db_result = result.scalar()
        
        from datetime import datetime
        return {
            'status': 'healthy',
            'task_id': task_id,
            'database_connection': bool(db_result),
            'worker_name': self.request.hostname,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Health check failed: {exc}")
        return {
            'status': 'unhealthy',
            'task_id': task_id,
            'error': str(exc),
            'worker_name': self.request.hostname
        }