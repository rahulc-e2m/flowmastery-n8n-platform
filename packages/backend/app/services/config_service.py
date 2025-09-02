"""
Config Service - Manages configuration operations with service layer protection
"""

import logging
from typing import Dict, Any
from datetime import datetime

from app.core.service_layer import BaseService, OperationContext, OperationType, OperationResult
from app.config import settings
from app.services.n8n.client import n8n_client

logger = logging.getLogger(__name__)


class ConfigService(BaseService[Dict[str, Any]]):
    """Service for managing configuration with full service layer protection"""
    
    @property
    def service_name(self) -> str:
        return "config_service"
    
    async def get_n8n_config_status(self, use_cache: bool = True) -> OperationResult[Dict[str, Any]]:
        """Get n8n configuration status"""
        context = OperationContext(operation_type=OperationType.READ)
        
        async def _get_n8n_config():
            # Check cache first
            if use_cache:
                cache_key = "n8n_config_status"
                cached_result = await self._get_from_cache(cache_key)
                if cached_result:
                    return cached_result
            
            try:
                # Check if configured
                if not settings.N8N_API_URL or not settings.N8N_API_KEY:
                    result = {
                        "configured": False,
                        "connection_healthy": False,
                        "message": "n8n not configured. Please set N8N_API_URL and N8N_API_KEY environment variables.",
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    # Test connection
                    start_time = datetime.now()
                    connection_healthy = await n8n_client.health_check()
                    response_time = (datetime.now() - start_time).total_seconds() * 1000
                    
                    # Mask API key for security
                    masked_key = self._mask_api_key(settings.N8N_API_KEY)
                    
                    result = {
                        "configured": True,
                        "connection_healthy": connection_healthy,
                        "instance_name": "n8n Instance",  # Could be made configurable
                        "api_url": settings.N8N_API_URL,
                        "masked_api_key": masked_key,
                        "response_time_ms": round(response_time, 2),
                        "timestamp": datetime.now().isoformat()
                    }
                
                # Cache for 60 seconds
                if use_cache:
                    await self._set_cache("n8n_config_status", result, ttl=60)
                
                return result
                
            except Exception as e:
                logger.error(f"Error checking n8n configuration: {e}")
                return {
                    "configured": bool(settings.N8N_API_URL and settings.N8N_API_KEY),
                    "connection_healthy": False,
                    "error": str(e),
                    "message": "Failed to check n8n configuration",
                    "timestamp": datetime.now().isoformat()
                }
        
        return await self.execute_operation(_get_n8n_config, context)
    
    async def get_ai_config_status(self, use_cache: bool = True) -> OperationResult[Dict[str, Any]]:
        """Get AI services configuration status"""
        context = OperationContext(operation_type=OperationType.READ)
        
        async def _get_ai_config():
            # Check cache first
            if use_cache:
                cache_key = "ai_config_status"
                cached_result = await self._get_from_cache(cache_key)
                if cached_result:
                    return cached_result
            
            result = {
                "gemini": {
                    "configured": bool(settings.GEMINI_API_KEY),
                    "status": "configured" if settings.GEMINI_API_KEY else "not_configured",
                    "masked_key": self._mask_api_key(settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else None
                },
                "openai": {
                    "configured": bool(settings.OPENAI_API_KEY),
                    "status": "configured" if settings.OPENAI_API_KEY else "not_configured",
                    "masked_key": self._mask_api_key(settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Cache for 5 minutes
            if use_cache:
                await self._set_cache("ai_config_status", result, ttl=300)
            
            return result
        
        return await self.execute_operation(_get_ai_config, context)
    
    async def get_app_config_status(self, use_cache: bool = True) -> OperationResult[Dict[str, Any]]:
        """Get application configuration status"""
        context = OperationContext(operation_type=OperationType.READ)
        
        async def _get_app_config():
            # Check cache first
            if use_cache:
                cache_key = "app_config_status"
                cached_result = await self._get_from_cache(cache_key)
                if cached_result:
                    return cached_result
            
            result = {
                "app_name": settings.APP_NAME,
                "app_version": settings.APP_VERSION,
                "debug": settings.DEBUG,
                "environment": {
                    "host": settings.BACKEND_HOST,
                    "port": settings.BACKEND_PORT,
                    "cors_origins": settings.CORS_ORIGINS,
                    "environment": settings.ENVIRONMENT
                },
                "services": {
                    "redis_url": self._mask_url(settings.REDIS_URL),
                    "cache_ttl": settings.CACHE_TTL,
                    "database_configured": bool(settings.DATABASE_URL)
                },
                "security": {
                    "rate_limit_per_minute": settings.RATE_LIMIT_PER_MINUTE,
                    "access_token_expire_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
                    "refresh_token_expire_days": settings.REFRESH_TOKEN_EXPIRE_DAYS
                },
                "monitoring": {
                    "enable_metrics": settings.ENABLE_METRICS,
                    "metrics_port": settings.METRICS_PORT,
                    "log_level": settings.LOG_LEVEL
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Cache for 10 minutes
            if use_cache:
                await self._set_cache("app_config_status", result, ttl=600)
            
            return result
        
        return await self.execute_operation(_get_app_config, context)
    
    async def get_full_config_status(self, use_cache: bool = True) -> OperationResult[Dict[str, Any]]:
        """Get comprehensive configuration status"""
        context = OperationContext(operation_type=OperationType.READ)
        
        async def _get_full_config():
            # Get all config sections
            n8n_result = await self.get_n8n_config_status(use_cache)
            ai_result = await self.get_ai_config_status(use_cache)
            app_result = await self.get_app_config_status(use_cache)
            
            # Combine results
            result = {
                "n8n": n8n_result.data if n8n_result.success else {"error": n8n_result.error},
                "ai": ai_result.data if ai_result.success else {"error": ai_result.error},
                "app": app_result.data if app_result.success else {"error": app_result.error},
                "overall_status": self._determine_config_health(n8n_result, ai_result, app_result),
                "timestamp": datetime.now().isoformat()
            }
            
            return result
        
        return await self.execute_operation(_get_full_config, context)
    
    def _mask_api_key(self, api_key: str) -> str:
        """Mask API key for security"""
        if not api_key:
            return ""
        
        if len(api_key) > 8:
            return api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]
        else:
            return "*" * len(api_key)
    
    def _mask_url(self, url: str) -> str:
        """Mask sensitive parts of URLs"""
        if not url:
            return ""
        
        # Simple masking - could be more sophisticated
        if "@" in url:
            parts = url.split("@")
            if len(parts) == 2:
                credentials = parts[0].split("://")
                if len(credentials) == 2:
                    protocol = credentials[0]
                    cred_part = credentials[1]
                    if ":" in cred_part:
                        user, password = cred_part.split(":", 1)
                        masked_creds = f"{user}:{'*' * len(password)}"
                        return f"{protocol}://{masked_creds}@{parts[1]}"
        
        return url
    
    def _determine_config_health(self, n8n_result, ai_result, app_result) -> str:
        """Determine overall configuration health"""
        if not all([n8n_result.success, ai_result.success, app_result.success]):
            return "error"
        
        # Check critical configurations
        if not n8n_result.data.get("configured"):
            return "incomplete"
        
        if not n8n_result.data.get("connection_healthy"):
            return "degraded"
        
        # Check if at least one AI service is configured
        ai_data = ai_result.data
        if not (ai_data.get("gemini", {}).get("configured") or ai_data.get("openai", {}).get("configured")):
            return "incomplete"
        
        return "healthy"


# Global service instance
config_service = ConfigService()