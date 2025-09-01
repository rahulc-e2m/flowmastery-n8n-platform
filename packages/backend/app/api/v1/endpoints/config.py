"""Configuration endpoints"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import Dict, Any

from app.config import settings
from app.services.n8n.client import n8n_client

router = APIRouter()


@router.get("/n8n/status")
async def get_n8n_config_status() -> Dict[str, Any]:
    """Get n8n configuration status"""
    
    try:
        # Check if configured
        if not settings.N8N_API_URL or not settings.N8N_API_KEY:
            return {
                "configured": False,
                "connection_healthy": False,
                "message": "n8n not configured. Please set N8N_API_URL and N8N_API_KEY environment variables."
            }
        
        # Test connection
        connection_healthy = await n8n_client.health_check()
        
        # Mask API key for security
        masked_key = ""
        if settings.N8N_API_KEY:
            key = settings.N8N_API_KEY
            if len(key) > 8:
                masked_key = key[:4] + "*" * (len(key) - 8) + key[-4:]
            else:
                masked_key = "*" * len(key)
        
        return {
            "configured": True,
            "connection_healthy": connection_healthy,
            "instance_name": "n8n Instance",  # Could be made configurable
            "api_url": settings.N8N_API_URL,
            "masked_api_key": masked_key,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "configured": bool(settings.N8N_API_URL and settings.N8N_API_KEY),
            "connection_healthy": False,
            "error": str(e),
            "message": "Failed to check n8n configuration",
            "timestamp": datetime.now().isoformat()
        }


@router.get("/ai/status")
async def get_ai_config_status() -> Dict[str, Any]:
    """Get AI services configuration status"""
    
    return {
        "gemini": {
            "configured": bool(settings.GEMINI_API_KEY),
            "status": "configured" if settings.GEMINI_API_KEY else "not_configured"
        },
        "openai": {
            "configured": bool(settings.OPENAI_API_KEY),
            "status": "configured" if settings.OPENAI_API_KEY else "not_configured"
        },
        "timestamp": datetime.now().isoformat()
    }


@router.get("/app/status")
async def get_app_config_status() -> Dict[str, Any]:
    """Get application configuration status"""
    
    return {
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "debug": settings.DEBUG,
        "environment": {
            "host": settings.BACKEND_HOST,
            "port": settings.BACKEND_PORT,
            "cors_origins": settings.CORS_ORIGINS
        },
        "services": {
            "redis_url": settings.REDIS_URL,
            "cache_ttl": settings.CACHE_TTL,
            "database_configured": bool(settings.DATABASE_URL)
        },
        "security": {
            "rate_limit_per_minute": settings.RATE_LIMIT_PER_MINUTE,
            "access_token_expire_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES
        },
        "monitoring": {
            "enable_metrics": settings.ENABLE_METRICS,
            "metrics_port": settings.METRICS_PORT,
            "log_level": settings.LOG_LEVEL
        },
        "timestamp": datetime.now().isoformat()
    }