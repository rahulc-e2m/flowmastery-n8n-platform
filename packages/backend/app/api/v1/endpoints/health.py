"""Health check endpoints with standardized responses"""

from fastapi import APIRouter, Request
from app.services.health_service import health_service
from app.core.response_formatter import format_response
from app.schemas.api_standard import HealthCheckResponse, HealthInfo

router = APIRouter()


@router.get("/", response_model=HealthCheckResponse)
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


@router.get("/detailed", response_model=HealthCheckResponse)
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


@router.get("/services")
@format_response(message="Service metrics retrieved successfully")
async def get_service_metrics(request: Request):
    """Get service performance metrics"""
    result = await health_service.get_service_metrics()
    
    if not result.success:
        # The decorator will handle the error formatting
        raise ValueError(result.error)
    
    return result.data