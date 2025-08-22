import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import time
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import threading

class N8nMetricsService:
    """Service to fetch and calculate n8n instance metrics"""
    
    def __init__(self, api_url: str = None, api_key: str = None):
        self.api_url = api_url
        self.api_key = api_key
    
    def configure(self, api_url: str, api_key: str) -> bool:
        """Configure API credentials and test connection"""
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        return self.test_connection()
    
    def test_connection(self) -> bool:
        """Test if the n8n API connection is working"""
        if not self.api_url or not self.api_key:
            return False
        
        try:
            response = self._make_request('GET', '/workflows', params={'limit': 1})
            return response.status_code == 200
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
    
    def _make_request(self, method: str, endpoint: str, params: dict = None, data: dict = None):
        """Make a request to the n8n API"""
        if not self.api_url or not self.api_key:
            raise ValueError("API URL and key must be configured")
        
        headers = {
            "accept": "application/json",
            "X-N8N-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }
        
        url = f"{self.api_url}{endpoint}"
        
        return requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=data,
            timeout=30
        )
    
    def get_workflows_metrics(self) -> Dict[str, Any]:
        """Get workflow-related metrics"""
        try:
            # Get all workflows
            response = self._make_request('GET', '/workflows', params={'limit': 250})
            if response.status_code != 200:
                return {"error": f"Failed to fetch workflows: {response.status_code}"}
            
            workflows_data = response.json()
            workflows = workflows_data.get('data', []) if isinstance(workflows_data, dict) else workflows_data
            
            total_workflows = len(workflows)
            active_workflows = sum(1 for wf in workflows if wf.get('active', False))
            inactive_workflows = total_workflows - active_workflows
            
            # Get workflow names for recent activity
            workflow_names = {wf.get('id'): wf.get('name', 'Unnamed') for wf in workflows}
            
            return {
                "total_workflows": total_workflows,
                "active_workflows": active_workflows,
                "inactive_workflows": inactive_workflows,
                "workflow_names": workflow_names
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_executions_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get execution-related metrics for the specified number of days"""
        try:
            # Calculate date range (n8n doesn't have date filtering, so we get recent executions)
            response = self._make_request('GET', '/executions', params={'limit': 250})
            if response.status_code != 200:
                return {"error": f"Failed to fetch executions: {response.status_code}"}
            
            executions_data = response.json()
            executions = executions_data.get('data', []) if isinstance(executions_data, dict) else executions_data
            
            # Filter executions by date (last N days)
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_executions = []
            
            for execution in executions:
                started_at = execution.get('startedAt')
                if started_at:
                    try:
                        # Parse ISO timestamp
                        exec_date = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
                        if exec_date.replace(tzinfo=None) > cutoff_date:
                            recent_executions.append(execution)
                    except:
                        # If date parsing fails, include it to be safe
                        recent_executions.append(execution)
            
            # Calculate metrics
            total_executions = len(recent_executions)
            success_executions = sum(1 for ex in recent_executions if ex.get('status') == 'success')
            error_executions = sum(1 for ex in recent_executions if ex.get('status') == 'error')
            waiting_executions = sum(1 for ex in recent_executions if ex.get('status') == 'waiting')
            
            success_rate = (success_executions / total_executions * 100) if total_executions > 0 else 0
            
            # Calculate daily execution counts
            daily_executions = {}
            for execution in recent_executions:
                started_at = execution.get('startedAt')
                if started_at:
                    try:
                        date_key = started_at[:10]  # YYYY-MM-DD
                        daily_executions[date_key] = daily_executions.get(date_key, 0) + 1
                    except:
                        pass
            
            # Get today's executions
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
            return {"error": str(e)}
    
    def get_users_metrics(self) -> Dict[str, Any]:
        """Get user-related metrics"""
        try:
            response = self._make_request('GET', '/users', params={'limit': 100})
            if response.status_code != 200:
                return {"error": f"Failed to fetch users: {response.status_code}"}
            
            users_data = response.json()
            users = users_data.get('data', []) if isinstance(users_data, dict) else users_data
            
            total_users = len(users)
            admin_users = sum(1 for user in users if user.get('role', {}).get('name') == 'global:admin')
            member_users = total_users - admin_users
            
            return {
                "total_users": total_users,
                "admin_users": admin_users,
                "member_users": member_users
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get additional system metrics"""
        try:
            metrics = {}
            
            # Get variables count
            try:
                response = self._make_request('GET', '/variables', params={'limit': 100})
                if response.status_code == 200:
                    variables_data = response.json()
                    variables = variables_data.get('data', []) if isinstance(variables_data, dict) else variables_data
                    metrics["total_variables"] = len(variables)
            except:
                metrics["total_variables"] = 0
            
            # Get tags count
            try:
                response = self._make_request('GET', '/tags', params={'limit': 100})
                if response.status_code == 200:
                    tags_data = response.json()
                    tags = tags_data.get('data', []) if isinstance(tags_data, dict) else tags_data
                    metrics["total_tags"] = len(tags)
            except:
                metrics["total_tags"] = 0
            
            return metrics
        except Exception as e:
            return {"error": str(e)}
    
    def get_comprehensive_metrics(self, execution_days: int = 7) -> Dict[str, Any]:
        """Get all metrics in a single call"""
        start_time = time.time()
        
        try:
            workflow_metrics = self.get_workflows_metrics()
            execution_metrics = self.get_executions_metrics(execution_days)
            user_metrics = self.get_users_metrics()
            system_metrics = self.get_system_metrics()
            
            # Calculate additional derived metrics
            total_workflows = workflow_metrics.get('total_workflows', 0)
            active_workflows = workflow_metrics.get('active_workflows', 0)
            total_executions = execution_metrics.get('total_executions', 0)
            success_rate = execution_metrics.get('success_rate', 0)
            
            # Estimate time saved (simplified calculation)
            # Assume each successful execution saves 10 minutes on average
            successful_executions = execution_metrics.get('success_executions', 0)
            estimated_time_saved = successful_executions * 10  # minutes
            time_saved_hours = round(estimated_time_saved / 60, 1)
            
            # Activity score (0-100 based on executions and active workflows)
            activity_score = min(100, (total_executions * 2 + active_workflows * 5))
            
            response_time = round(time.time() - start_time, 2)
            
            return {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "response_time": response_time,
                "connection_healthy": True,
                "workflows": workflow_metrics,
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
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "response_time": round(time.time() - start_time, 2),
                "connection_healthy": False
            }

    def _fetch_single_metric(self, endpoint: str, params: dict = None) -> Dict[str, Any]:
        """Fetch a single metric endpoint"""
        try:
            response = self._make_request('GET', endpoint, params=params)
            if response.status_code == 200:
                data = response.json()
                return {"success": True, "data": data}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_fast_metrics(self) -> Dict[str, Any]:
        """Get essential metrics with parallel API calls for fast loading"""
        start_time = time.time()
        
        try:
            # Use ThreadPoolExecutor to make parallel API calls
            with ThreadPoolExecutor(max_workers=4) as executor:
                # Submit all API calls simultaneously with higher limits for better accuracy
                workflows_future = executor.submit(self._fetch_single_metric, '/workflows', {'limit': 250})
                executions_future = executor.submit(self._fetch_single_metric, '/executions', {'limit': 100})
                users_future = executor.submit(self._fetch_single_metric, '/users', {'limit': 100})
                variables_future = executor.submit(self._fetch_single_metric, '/variables', {'limit': 50})
                
                # Wait for all results with error handling
                try:
                    workflows_result = workflows_future.result(timeout=15)
                except Exception as e:
                    workflows_result = {"success": False, "error": str(e)}
                
                try:
                    executions_result = executions_future.result(timeout=15)
                except Exception as e:
                    executions_result = {"success": False, "error": str(e)}
                
                try:
                    users_result = users_future.result(timeout=15)
                except Exception as e:
                    users_result = {"success": False, "error": str(e)}
                
                try:
                    variables_result = variables_future.result(timeout=15)
                except Exception as e:
                    variables_result = {"success": False, "error": str(e)}
            
            # Process workflows data
            if workflows_result["success"]:
                workflows_data = workflows_result["data"]
                workflows = workflows_data.get('data', []) if isinstance(workflows_data, dict) else workflows_data
                total_workflows = len(workflows)
                active_workflows = sum(1 for wf in workflows if wf.get('active', False))
                inactive_workflows = total_workflows - active_workflows
            else:
                total_workflows = active_workflows = inactive_workflows = 0
            
            # Process executions data (quick calculation)
            if executions_result["success"]:
                executions_data = executions_result["data"]
                executions = executions_data.get('data', []) if isinstance(executions_data, dict) else executions_data
                
                # Quick calculation for recent executions (just today)
                today = datetime.now().strftime('%Y-%m-%d')
                today_executions = 0
                success_count = 0
                total_count = 0
                
                # Process all fetched executions for better accuracy
                for execution in executions:
                    started_at = execution.get('startedAt')
                    if started_at and started_at.startswith(today):
                        today_executions += 1
                    
                    # Count for success rate
                    total_count += 1
                    status = execution.get('status', '').lower()
                    if status in ['success', 'finished']:
                        success_count += 1
                
                success_rate = (success_count / total_count * 100) if total_count > 0 else 0
            else:
                today_executions = success_rate = 0
            
            # Process users data
            if users_result["success"]:
                users_data = users_result["data"]
                users = users_data.get('data', []) if isinstance(users_data, dict) else users_data
                total_users = len(users)
                admin_users = sum(1 for user in users if user.get('role', {}).get('name') == 'global:admin')
            else:
                total_users = admin_users = 0
            
            # Process variables (simplified) - handle 403 errors gracefully
            if variables_result["success"]:
                variables_data = variables_result["data"]
                variables = variables_data.get('data', []) if isinstance(variables_data, dict) else variables_data
                total_variables = len(variables)
            else:
                # Variables endpoint may not be accessible (403 Forbidden)
                # This is normal for some n8n instances, so we continue without failing
                total_variables = 0
            
            # Calculate quick derived metrics
            time_saved_hours = round(success_count * 0.2, 1)  # Quick estimate
            activity_score = min(100, (today_executions * 10 + active_workflows * 5))
            
            response_time = round(time.time() - start_time, 2)
            
            return {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "response_time": response_time,
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
                    "total_tags": 0  # Skip tags for speed
                },
                "derived_metrics": {
                    "time_saved_hours": time_saved_hours,
                    "activity_score": activity_score,
                    "automation_efficiency": round(success_rate, 1),
                    "workflows_per_user": round(total_workflows / max(1, total_users), 1),
                    "executions_per_workflow": round(total_count / max(1, active_workflows), 1) if active_workflows > 0 else 0
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "response_time": round(time.time() - start_time, 2),
                "connection_healthy": False
            }


# Simple in-memory cache for metrics
class MetricsCache:
    def __init__(self, ttl_seconds: int = 30):
        self.cache = {}
        self.ttl = ttl_seconds
        self.lock = threading.Lock()
    
    def get(self, key: str):
        with self.lock:
            if key in self.cache:
                data, timestamp = self.cache[key]
                if time.time() - timestamp < self.ttl:
                    return data
                else:
                    del self.cache[key]
            return None
    
    def set(self, key: str, value):
        with self.lock:
            self.cache[key] = (value, time.time())
    
    def clear(self):
        with self.lock:
            self.cache.clear()


# Global instances
metrics_service = N8nMetricsService()
metrics_cache = MetricsCache(ttl_seconds=45)  # Cache for 45 seconds
