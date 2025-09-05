"""System administration endpoints with health and configuration monitoring"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

from app.database import get_db
from app.models.user import User
from app.core.dependencies import get_current_user
from app.core.user_roles import UserRole
from app.services.persistent_metrics import persistent_metrics_collector
from app.services.health_service import health_service
from app.services.config_service import config_service
from app.core.decorators import validate_input, sanitize_response
from app.core.response_formatter import format_response
from app.schemas.api_standard import HealthCheckResponse, HealthInfo

router = APIRouter()


# Health check endpoints
@router.get("/health", response_model=HealthCheckResponse, tags=["health"])
@format_response(message="Health check completed successfully")
async def health_check(request: Request):
    """Basic health check"""
    result = await health_service.get_basic_health()
    
    if not result.success:
        # The decorator will handle the error formatting
        raise ValueError(result.error)
    
    # Convert to standardized health info
    health_info = HealthInfo(
        status=result.data.get("status", "unknown"),
        version=result.data.get("version", "unknown"),
        timestamp=result.data.get("timestamp")
    )
    
    return health_info


@router.get("/health/detailed", response_model=HealthCheckResponse, tags=["health"])
@format_response(message="Detailed health check completed successfully")
async def detailed_health_check(request: Request):
    """Detailed health check with service status"""
    result = await health_service.get_detailed_health()
    
    if not result.success:
        # The decorator will handle the error formatting
        raise ValueError(result.error)
    
    # Convert to standardized health info
    health_info = HealthInfo(
        status=result.data.get("status", "unknown"),
        version=result.data.get("version", "unknown"),
        timestamp=result.data.get("timestamp")
    )
    
    return health_info


@router.get("/health/services", tags=["health"])
@format_response(message="Service metrics retrieved successfully")
async def get_service_metrics(request: Request):
    """Get service performance metrics"""
    result = await health_service.get_service_metrics()
    
    if not result.success:
        # The decorator will handle the error formatting
        raise ValueError(result.error)
    
    return result.data


class SyncRequest(BaseModel):
    """Request model for sync operations"""
    type: Literal["client", "all", "quick"]
    client_id: Optional[str] = None
    options: Optional[Dict[str, Any]] = None


@router.post("/sync")
@validate_input(max_string_length=100)
@sanitize_response()
@format_response(message="Sync operation completed successfully")
async def sync_operations(
    sync_request: SyncRequest,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_user(required_roles=[UserRole.ADMIN]))
):
    """Consolidated sync operations - replaces multiple sync endpoints"""
    
    try:
        if sync_request.type == "client":
            # Sync specific client
            if not sync_request.client_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="client_id is required for client sync"
                )
            
            result = await persistent_metrics_collector.sync_client_data(
                db, sync_request.client_id
            )
            
            return {
                "message": f"Successfully synced client {sync_request.client_id}",
                "type": "client",
                "client_id": sync_request.client_id,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        elif sync_request.type == "all":
            # Sync all clients
            result = await persistent_metrics_collector.sync_all_clients(db)
            
            return {
                "message": "Successfully synced all clients",
                "type": "all",
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        elif sync_request.type == "quick":
            # Quick sync all clients with cache warming
            from app.services.cache.redis import redis_client
            from app.services.metrics_service import metrics_service
            from sqlalchemy import select
            from app.models import Client
            
            # Clear all cache first
            await redis_client.clear_pattern("enhanced_client_metrics:*")
            await redis_client.clear_pattern("client_metrics:*")
            await redis_client.clear_pattern("admin_metrics:*")
            
            # Sync all clients immediately
            results = []
            
            # Get all clients with n8n configuration
            stmt = select(Client).where(
                Client.n8n_api_url.isnot(None)
            )
            result = await db.execute(stmt)
            clients = result.scalars().all()
            
            for client in clients:
                try:
                    sync_result = await persistent_metrics_collector.sync_client_data(
                        db, client.id
                    )
                    results.append({
                        "client_id": client.id,
                        "client_name": client.name,
                        "status": "success",
                        "result": sync_result
                    })
                    
                    # Warm cache for this client immediately after sync
                    try:
                        await metrics_service.get_client_metrics(db, client.id, use_cache=False)
                    except Exception as cache_error:
                        logger.warning(f"Failed to warm cache for client {client.id}: {cache_error}")
                        
                except Exception as e:
                    results.append({
                        "client_id": client.id,
                        "client_name": client.name,
                        "status": "error",
                        "error": str(e)
                    })
            
            # Commit all changes
            await db.commit()
            
            # Warm admin metrics cache
            try:
                await metrics_service.get_admin_metrics(db)
            except Exception as cache_error:
                logger.warning(f"Failed to warm admin metrics cache: {cache_error}")
            
            successful = [r for r in results if r["status"] == "success"]
            failed = [r for r in results if r["status"] == "error"]
            
            return {
                "message": f"Quick sync completed: {len(successful)} successful, {len(failed)} failed",
                "type": "quick",
                "successful": len(successful),
                "failed": len(failed),
                "results": results,
                "timestamp": datetime.utcnow().isoformat(),
                "cache_warmed": True
            }
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid sync type: {sync_request.type}"
            )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )






# Configuration endpoints
@router.get("/config", tags=["config"])
@format_response(message="System configuration retrieved successfully")
async def get_system_config(
    admin_user: User = Depends(get_current_user(required_roles=[UserRole.ADMIN]))
):
    """Get comprehensive system configuration status (admin only)"""
    
    try:
        result = await config_service.get_full_config_status()
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get configuration status: {result.error}"
            )
        
        return result.data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system configuration: {str(e)}"
        )


@router.get("/config/n8n", tags=["config"])
@format_response(message="n8n configuration status retrieved successfully")
async def get_n8n_config(
    admin_user: User = Depends(get_current_user(required_roles=[UserRole.ADMIN]))
):
    """Get n8n configuration status (admin only)"""
    
    try:
        result = await config_service.get_n8n_config_status()
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get n8n configuration: {result.error}"
            )
        
        return result.data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get n8n configuration: {str(e)}"
        )


@router.get("/config/ai", tags=["config"])
@format_response(message="AI services configuration status retrieved successfully")
async def get_ai_config(
    admin_user: User = Depends(get_current_user(required_roles=[UserRole.ADMIN]))
):
    """Get AI services configuration status (admin only)"""
    
    try:
        result = await config_service.get_ai_config_status()
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get AI configuration: {result.error}"
            )
        
        return result.data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get AI configuration: {str(e)}"
        )


@router.get("/config/app", tags=["config"])
@format_response(message="Application configuration status retrieved successfully")
async def get_app_config(
    admin_user: User = Depends(get_current_user(required_roles=[UserRole.ADMIN]))
):
    """Get application configuration status (admin only)"""
    
    try:
        result = await config_service.get_app_config_status()
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get app configuration: {result.error}"
            )
        
        return result.data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get app configuration: {str(e)}"
        )
