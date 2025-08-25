"""Metrics endpoints"""

from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from typing import Dict, Any

from app.services.n8n.metrics import metrics_service
from app.services.n8n.client import n8n_client
from app.config import settings
from app.core.exceptions import N8nConnectionError

router = APIRouter()


@router.get("/fast")
async def get_fast_metrics() -> Dict[str, Any]:
    """Get essential metrics with fast loading and caching"""
    
    # Check if n8n is configured
    if not settings.N8N_API_URL or not settings.N8N_API_KEY:
        # Return mock data when not configured
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "response_time": 0.1,
            "connection_healthy": True,
            "workflows": {
                "total_workflows": 5,
                "active_workflows": 3,
                "inactive_workflows": 2
            },
            "executions": {
                "today_executions": 12,
                "success_rate": 94.7,
                "total_executions": 150,
                "success_executions": 142,
                "error_executions": 8
            },
            "users": {
                "total_users": 2,
                "admin_users": 1,
                "member_users": 1
            },
            "system": {
                "total_variables": 3,
                "total_tags": 0
            },
            "derived_metrics": {
                "time_saved_hours": 24.0,
                "activity_score": 85,
                "automation_efficiency": 94.7,
                "workflows_per_user": 2.5,
                "executions_per_workflow": 30.0
            },
            "mock_data": True
        }
    
    try:
        metrics = await metrics_service.get_fast_metrics()
        
        if metrics.get("status") == "error":
            raise HTTPException(status_code=500, detail=metrics.get("error"))
        
        return metrics
        
    except N8nConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/dashboard")
async def get_dashboard_metrics(
    execution_days: int = Query(7, ge=1, le=30, description="Number of days for execution metrics")
) -> Dict[str, Any]:
    """Get comprehensive dashboard metrics"""
    
    # Check if n8n is configured
    if not settings.N8N_API_URL or not settings.N8N_API_KEY:
        # Return mock data when not configured
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "response_time": 0.1,
            "connection_healthy": True,
            "workflows": {
                "total_workflows": 5,
                "active_workflows": 3,
                "inactive_workflows": 2,
                "workflow_names": {
                    "1": "Data Sync Workflow",
                    "2": "Email Automation",
                    "3": "Report Generator"
                }
            },
            "executions": {
                "total_executions": 150,
                "success_executions": 142,
                "error_executions": 8,
                "waiting_executions": 0,
                "success_rate": 94.7,
                "today_executions": 12,
                "daily_executions": {
                    datetime.now().strftime('%Y-%m-%d'): 12
                },
                "period_days": execution_days
            },
            "users": {
                "total_users": 2,
                "admin_users": 1,
                "member_users": 1
            },
            "system": {
                "total_variables": 3,
                "total_tags": 5
            },
            "derived_metrics": {
                "time_saved_hours": 24.0,
                "activity_score": 85,
                "automation_efficiency": 94.7,
                "workflows_per_user": 2.5,
                "executions_per_workflow": 30.0
            },
            "mock_data": True
        }
    
    try:
        metrics = await metrics_service.get_comprehensive_metrics(execution_days)
        
        if metrics.get("status") == "error":
            raise HTTPException(status_code=500, detail=metrics.get("error"))
        
        return metrics
        
    except N8nConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard metrics: {str(e)}")


@router.get("/workflows")
async def get_workflow_metrics() -> Dict[str, Any]:
    """Get workflow-specific metrics"""
    
    if not settings.N8N_API_URL or not settings.N8N_API_KEY:
        raise HTTPException(status_code=400, detail="n8n not configured")
    
    try:
        metrics = await metrics_service.get_workflows_metrics()
        
        if "error" in metrics:
            raise HTTPException(status_code=500, detail=metrics["error"])
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "data": metrics
        }
        
    except N8nConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflow metrics: {str(e)}")


@router.get("/executions")
async def get_execution_metrics(
    days: int = Query(7, ge=1, le=30, description="Number of days for execution metrics")
) -> Dict[str, Any]:
    """Get execution-specific metrics"""
    
    if not settings.N8N_API_URL or not settings.N8N_API_KEY:
        raise HTTPException(status_code=400, detail="n8n not configured")
    
    try:
        metrics = await metrics_service.get_executions_metrics(days)
        
        if "error" in metrics:
            raise HTTPException(status_code=500, detail=metrics["error"])
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "data": metrics
        }
        
    except N8nConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get execution metrics: {str(e)}")


@router.get("/users")
async def get_user_metrics() -> Dict[str, Any]:
    """Get user-specific metrics"""
    
    if not settings.N8N_API_URL or not settings.N8N_API_KEY:
        raise HTTPException(status_code=400, detail="n8n not configured")
    
    try:
        metrics = await metrics_service.get_users_metrics()
        
        if "error" in metrics:
            raise HTTPException(status_code=500, detail=metrics["error"])
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "data": metrics
        }
        
    except N8nConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user metrics: {str(e)}")


@router.get("/system")
async def get_system_metrics() -> Dict[str, Any]:
    """Get system-specific metrics"""
    
    if not settings.N8N_API_URL or not settings.N8N_API_KEY:
        raise HTTPException(status_code=400, detail="n8n not configured")
    
    try:
        metrics = await metrics_service.get_system_metrics()
        
        if "error" in metrics:
            raise HTTPException(status_code=500, detail=metrics["error"])
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "data": metrics
        }
        
    except N8nConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system metrics: {str(e)}")