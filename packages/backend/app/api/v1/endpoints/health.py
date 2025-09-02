"""Health check endpoints"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.services.health_service import health_service

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    services: dict


@router.get("/", response_model=HealthResponse)
async def health_check():
    """Basic health check"""
    result = await health_service.get_basic_health()
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error
        )
    
    return HealthResponse(**result.data)


@router.get("/detailed", response_model=HealthResponse)
async def detailed_health_check():
    """Detailed health check with service status"""
    result = await health_service.get_detailed_health()
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error
        )
    
    return HealthResponse(**result.data)


@router.get("/services")
async def get_service_metrics():
    """Get service performance metrics"""
    result = await health_service.get_service_metrics()
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error
        )
    
    return result.data