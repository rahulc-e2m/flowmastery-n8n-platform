"""n8n metrics service"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

from app.services.n8n.client import n8n_client
from app.services.cache.redis import redis_client
from app.core.exceptions import N8nConnectionError

logger = logging.getLogger(__name__)


class MetricsService:
    """Service for collecting and calculating n8n metrics"""
    
    def __init__(self):
        self.cache_ttl = 45  # Cache for 45 seconds
    
    async def get_workflows_metrics(self) -> Dict[str, Any]:
        """Get workflow-related metrics"""
        try:
            workflows = await n8n_client.get_workflows(limit=250)
            
            total_workflows = len(workflows)
            active_workflows = sum(1 for wf in workflows if wf.get('active', False))
            inactive_workflows = total_workflows - active_workflows
            
            # Create workflow name mapping
            workflow_names = {wf.get('id'): wf.get('name', 'Unnamed') for wf in workflows}
            
            return {
                "total_workflows": total_workflows,
                "active_workflows": active_workflows,
                "inactive_workflows": inactive_workflows,
                "workflow_names": workflow_names
            }
        except Exception as e:
            logger.error(f"Failed to get workflow metrics: {e}")
            return {"error": str(e)}
    
    async def get_executions_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get execution-related metrics"""
        try:
            # Get recent executions
            executions = await n8n_client.get_executions(limit=250)
            
            # Filter by date range
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_executions = []
            
            for execution in executions:
                started_at = execution.get('startedAt')
                if started_at:
                    try:
                        exec_date = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
                        if exec_date.replace(tzinfo=None) > cutoff_date:
                            recent_executions.append(execution)
                    except:
                        recent_executions.append(execution)
            
            # Calculate metrics
            total_executions = len(recent_executions)
            success_executions = sum(1 for ex in recent_executions if ex.get('status') == 'success')
            error_executions = sum(1 for ex in recent_executions if ex.get('status') == 'error')
            waiting_executions = sum(1 for ex in recent_executions if ex.get('status') == 'waiting')
            
            success_rate = (success_executions / total_executions * 100) if total_executions > 0 else 0
            
            # Daily execution counts
            daily_executions = {}
            for execution in recent_executions:
                started_at = execution.get('startedAt')
                if started_at:
                    try:
                        date_key = started_at[:10]  # YYYY-MM-DD
                        daily_executions[date_key] = daily_executions.get(date_key, 0) + 1
                    except:
                        pass
            
            # Today's executions
            today = datetime.now().strftime('%Y-%m-%d')
            today_executions = daily_executions.get(today, 0)
            
            return {
                "total_executions": total_executions,
                "success_executions": success_executions,
                "error_executions": error_executions,
                "waiting_executions": waiting_executions,
                "success_rate": round(success_rate, 1),
                "today_executions": today_executions,
                "daily_executions": daily_executions,
                "period_days": days
            }
        except Exception as e:
            logger.error(f"Failed to get execution metrics: {e}")
            return {"error": str(e)}
    
    async def get_users_metrics(self) -> Dict[str, Any]:
        """Get user-related metrics"""
        try:
            users = await n8n_client.get_users(limit=100)
            
            total_users = len(users)
            admin_users = sum(1 for user in users if user.get('role', {}).get('name') == 'global:admin')
            member_users = total_users - admin_users
            
            return {
                "total_users": total_users,
                "admin_users": admin_users,
                "member_users": member_users
            }
        except Exception as e:
            logger.error(f"Failed to get user metrics: {e}")
            return {"error": str(e)}
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get system-related metrics"""
        try:
            # Run in parallel
            variables_task = n8n_client.get_variables(limit=100)
            tags_task = n8n_client.get_tags(limit=100)
            
            variables, tags = await asyncio.gather(
                variables_task, tags_task, return_exceptions=True
            )
            
            # Handle results
            total_variables = len(variables) if not isinstance(variables, Exception) else 0
            total_tags = len(tags) if not isinstance(tags, Exception) else 0
            
            return {
                "total_variables": total_variables,
                "total_tags": total_tags
            }
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {"error": str(e)}
    
    async def get_fast_metrics(self) -> Dict[str, Any]:
        """Get essential metrics with caching and parallel requests"""
        cache_key = "fast_metrics"
        
        # Try cache first
        try:
            cached = await redis_client.get(cache_key)
            if cached:
                return cached
        except Exception as e:
            logger.warning(f"Cache read failed: {e}")
        
        try:
            # Run all requests in parallel
            workflows_task = n8n_client.get_workflows(limit=250)
            executions_task = n8n_client.get_executions(limit=100)
            users_task = n8n_client.get_users(limit=100)
            variables_task = n8n_client.get_variables(limit=50)
            
            start_time = datetime.now()
            
            # Wait for all with timeout
            workflows, executions, users, variables = await asyncio.gather(
                workflows_task, executions_task, users_task, variables_task,
                return_exceptions=True
            )
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Process workflows
            if not isinstance(workflows, Exception):
                total_workflows = len(workflows)
                active_workflows = sum(1 for wf in workflows if wf.get('active', False))
                inactive_workflows = total_workflows - active_workflows
            else:
                total_workflows = active_workflows = inactive_workflows = 0
            
            # Process executions (quick calculation)
            if not isinstance(executions, Exception):
                today = datetime.now().strftime('%Y-%m-%d')
                today_executions = 0
                success_count = 0
                total_count = len(executions)
                
                for execution in executions:
                    started_at = execution.get('startedAt', '')
                    if started_at.startswith(today):
                        today_executions += 1
                    
                    status = execution.get('status', '').lower()
                    if status in ['success', 'finished']:
                        success_count += 1
                
                success_rate = (success_count / total_count * 100) if total_count > 0 else 0
            else:
                today_executions = success_rate = total_count = success_count = 0
            
            # Process users
            if not isinstance(users, Exception):
                total_users = len(users)
                admin_users = sum(1 for user in users if user.get('role', {}).get('name') == 'global:admin')
            else:
                total_users = admin_users = 0
            
            # Process variables
            total_variables = len(variables) if not isinstance(variables, Exception) else 0
            
            # Calculate derived metrics
            time_saved_hours = round(success_count * 0.2, 1)
            activity_score = min(100, (today_executions * 10 + active_workflows * 5))
            
            result = {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "response_time": round(response_time, 2),
                "connection_healthy": True,
                "workflows": {
                    "total_workflows": total_workflows,
                    "active_workflows": active_workflows,
                    "inactive_workflows": inactive_workflows
                },
                "executions": {
                    "today_executions": today_executions,
                    "success_rate": round(success_rate, 1),
                    "total_executions": total_count,
                    "success_executions": success_count,
                    "error_executions": total_count - success_count
                },
                "users": {
                    "total_users": total_users,
                    "admin_users": admin_users,
                    "member_users": total_users - admin_users
                },
                "system": {
                    "total_variables": total_variables,
                    "total_tags": 0  # Skip for speed
                },
                "derived_metrics": {
                    "time_saved_hours": time_saved_hours,
                    "activity_score": activity_score,
                    "automation_efficiency": round(success_rate, 1),
                    "workflows_per_user": round(total_workflows / max(1, total_users), 1),
                    "executions_per_workflow": round(total_count / max(1, active_workflows), 1) if active_workflows > 0 else 0
                }
            }
            
            # Cache the result
            try:
                await redis_client.set(cache_key, result, expire=self.cache_ttl)
            except Exception as e:
                logger.warning(f"Cache write failed: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get fast metrics: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "connection_healthy": False
            }
    
    async def get_comprehensive_metrics(self, execution_days: int = 7) -> Dict[str, Any]:
        """Get comprehensive dashboard metrics with caching"""
        cache_key = f"dashboard_metrics_{execution_days}"
        
        # Try cache first
        try:
            cached = await redis_client.get(cache_key)
            if cached:
                return cached
        except Exception as e:
            logger.warning(f"Cache read failed: {e}")
        
        try:
            start_time = datetime.now()
            
            # Get all metrics
            workflows_metrics = await self.get_workflows_metrics()
            execution_metrics = await self.get_executions_metrics(execution_days)
            user_metrics = await self.get_users_metrics()
            system_metrics = await self.get_system_metrics()
            
            # Calculate derived metrics
            total_workflows = workflows_metrics.get('total_workflows', 0)
            active_workflows = workflows_metrics.get('active_workflows', 0)
            total_executions = execution_metrics.get('total_executions', 0)
            success_rate = execution_metrics.get('success_rate', 0)
            successful_executions = execution_metrics.get('success_executions', 0)
            
            # Time saved estimation (10 minutes per successful execution)
            time_saved_hours = round(successful_executions * 10 / 60, 1)
            
            # Activity score
            activity_score = min(100, (total_executions * 2 + active_workflows * 5))
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "response_time": round(response_time, 2),
                "connection_healthy": True,
                "workflows": workflows_metrics,
                "executions": execution_metrics,
                "users": user_metrics,
                "system": system_metrics,
                "derived_metrics": {
                    "time_saved_hours": time_saved_hours,
                    "activity_score": activity_score,
                    "automation_efficiency": success_rate,
                    "workflows_per_user": round(total_workflows / max(1, user_metrics.get('total_users', 1)), 1),
                    "executions_per_workflow": round(total_executions / max(1, active_workflows), 1) if active_workflows > 0 else 0
                }
            }
            
            # Cache the result
            try:
                await redis_client.set(cache_key, result, expire=self.cache_ttl)
            except Exception as e:
                logger.warning(f"Cache write failed: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get comprehensive metrics: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "response_time": 0,
                "connection_healthy": False
            }


# Global service instance
metrics_service = MetricsService()