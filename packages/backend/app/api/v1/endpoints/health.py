"""Health check endpoints"""

from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel

from app.config import settings
from app.services.n8n.client import n8n_client
from app.services.cache.redis import redis_client

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    services: dict


@router.get("/", response_model=HealthResponse)
async def health_check():
    """Basic health check"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version=settings.APP_VERSION,
        services={}
    )


@router.get("/detailed", response_model=HealthResponse)
async def detailed_health_check():
    """Detailed health check with service status"""
    services = {}
    
    # Check Redis
    try:
        redis_healthy = await redis_client.ping()
        services["redis"] = {
            "status": "healthy" if redis_healthy else "unhealthy",
            "url": settings.REDIS_URL
        }
    except Exception as e:
        services["redis"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Check n8n
    try:
        if settings.N8N_API_URL and settings.N8N_API_KEY:
            n8n_healthy = await n8n_client.health_check()
            services["n8n"] = {
                "status": "healthy" if n8n_healthy else "unhealthy",
                "url": settings.N8N_API_URL,
                "configured": True
            }
        else:
            services["n8n"] = {
                "status": "not_configured",
                "configured": False
            }
    except Exception as e:
        services["n8n"] = {
            "status": "error",
            "error": str(e),
            "configured": bool(settings.N8N_API_URL and settings.N8N_API_KEY)
        }
    
    # Check AI services
    services["ai"] = {
        "gemini": {
            "configured": bool(settings.GEMINI_API_KEY),
            "status": "configured" if settings.GEMINI_API_KEY else "not_configured"
        },
        "openai": {
            "configured": bool(settings.OPENAI_API_KEY),
            "status": "configured" if settings.OPENAI_API_KEY else "not_configured"
        }
    }
    
    # Overall status
    overall_status = "healthy"
    if any(service.get("status") == "error" for service in services.values() if isinstance(service, dict)):
        overall_status = "degraded"
    elif any(service.get("status") == "unhealthy" for service in services.values() if isinstance(service, dict)):
        overall_status = "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now().isoformat(),
        version=settings.APP_VERSION,
        services=services
    )