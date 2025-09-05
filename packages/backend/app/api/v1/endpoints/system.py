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
@router.get("/health", response_model=HealthCheckResponse)
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


@router.get("/health/detailed", response_model=HealthCheckResponse)
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


@router.get("/health/services")
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
        from app.services.system_service import system_service
        from app.core.service_layer import OperationContext, OperationType
        
        # Create operation context
        context = OperationContext(
            operation_type=OperationType.UPDATE,
            user_id=admin_user.id
        )
        
        if sync_request.type == "client":
            # Sync specific client
            if not sync_request.client_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="client_id is required for client sync"
                )
            
            result = await system_service.sync_client_data(
                db, sync_request.client_id, context
            )
            
            if not result.success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error or "Failed to sync client"
                )
            
            return result.data
        
        elif sync_request.type == "all":
            # Sync all clients
            result = await system_service.sync_all_clients(db, context)
            
            if not result.success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error or "Failed to sync all clients"
                )
            
            return result.data
        
        elif sync_request.type == "quick":
            # Quick sync all clients with cache warming
            result = await system_service.quick_sync_with_cache_warm(db, context)
            
            if not result.success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error or "Failed to perform quick sync"
                )
            
            return result.data
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid sync type: {sync_request.type}"
            )
    
    except HTTPException:
        raise
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
