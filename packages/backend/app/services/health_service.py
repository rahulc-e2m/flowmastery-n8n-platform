"""
Health Service - Manages health check operations with service layer protection
"""

import logging
from typing import Dict, Any
from datetime import datetime, timezone

from app.core.service_layer import BaseService, OperationContext, OperationType, OperationResult
from app.config import settings
from app.services.n8n.client import n8n_client
from app.services.cache.redis import redis_client

logger = logging.getLogger(__name__)


class HealthService(BaseService[Dict[str, Any]]):
    """Service for managing health checks with full service layer protection"""
    
    @property
    def service_name(self) -> str:
        return "health_service"
    
    async def get_basic_health(self) -> OperationResult[Dict[str, Any]]:
        """Get basic health status"""
        context = OperationContext(operation_type=OperationType.READ)
        
        async def _get_basic_health():
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": settings.APP_VERSION,
                "services": {}
            }
        
        return await self.execute_operation(_get_basic_health, context)
    
    async def get_detailed_health(self, use_cache: bool = True) -> OperationResult[Dict[str, Any]]:
        """Get detailed health status with service checks"""
        context = OperationContext(operation_type=OperationType.READ)
        
        async def _get_detailed_health():
            # Check cache first
            if use_cache:
                cache_key = "detailed_health_status"
                cached_result = await self._get_from_cache(cache_key)
                if cached_result:
                    return cached_result
            
            services = {}
            
            # Check Redis
            redis_status = await self._check_redis_health()
            services["redis"] = redis_status
            
            # Check n8n
            n8n_status = await self._check_n8n_health()
            services["n8n"] = n8n_status
            
            # Check AI services
            ai_status = await self._check_ai_services_health()
            services["ai"] = ai_status
            
            # Overall status determination
            overall_status = self._determine_overall_status(services)
            
            result = {
                "status": overall_status,
                "timestamp": datetime.now().isoformat(),
                "version": settings.APP_VERSION,
                "services": services
            }
            
            # Cache the result for 30 seconds
            if use_cache:
                await self._set_cache("detailed_health_status", result, ttl=30)
            
            return result
        
        return await self.execute_operation(_get_detailed_health, context)
    
    async def _check_redis_health(self) -> Dict[str, Any]:
        """Check Redis service health"""
        try:
            redis_healthy = await redis_client.ping()
            return {
                "status": "healthy" if redis_healthy else "unhealthy",
                "url": settings.REDIS_URL,
                "response_time_ms": None  # Could add timing if needed
            }
        except Exception as e:
            logger.warning(f"Redis health check failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "url": settings.REDIS_URL
            }
    
    async def _check_n8n_health(self) -> Dict[str, Any]:
        """Check n8n service health"""
        try:
            if settings.N8N_API_URL and settings.N8N_API_KEY:
                start_time = datetime.now()
                n8n_healthy = await n8n_client.health_check()
                response_time = (datetime.now() - start_time).total_seconds() * 1000
                
                return {
                    "status": "healthy" if n8n_healthy else "unhealthy",
                    "url": settings.N8N_API_URL,
                    "configured": True,
                    "response_time_ms": round(response_time, 2)
                }
            else:
                return {
                    "status": "not_configured",
                    "configured": False,
                    "url": None
                }
        except Exception as e:
            logger.warning(f"n8n health check failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "configured": bool(settings.N8N_API_URL and settings.N8N_API_KEY),
                "url": settings.N8N_API_URL
            }
    
    async def _check_ai_services_health(self) -> Dict[str, Any]:
        """Check AI services configuration status"""
        return {
            "gemini": {
                "configured": bool(settings.GEMINI_API_KEY),
                "status": "configured" if settings.GEMINI_API_KEY else "not_configured"
            },
            "openai": {
                "configured": bool(settings.OPENAI_API_KEY),
                "status": "configured" if settings.OPENAI_API_KEY else "not_configured"
            }
        }
    
    def _determine_overall_status(self, services: Dict[str, Any]) -> str:
        """Determine overall system health status"""
        # Check for critical service failures
        critical_services = ["redis"]
        
        for service_name in critical_services:
            if service_name in services:
                service_status = services[service_name].get("status")
                if service_status == "error":
                    return "critical"
                elif service_status == "unhealthy":
                    return "unhealthy"
        
        # Check for degraded services
        for service_name, service_data in services.items():
            if isinstance(service_data, dict):
                service_status = service_data.get("status")
                if service_status == "error":
                    return "degraded"
                elif service_status == "unhealthy":
                    return "degraded"
        
        return "healthy"
    
    async def get_service_metrics(self) -> OperationResult[Dict[str, Any]]:
        """Get service performance metrics"""
        context = OperationContext(operation_type=OperationType.READ)
        
        async def _get_service_metrics():
            try:
                # Get Redis info
                redis_info = {}
                try:
                    redis_info = await redis_client.info()
                except Exception as e:
                    logger.warning(f"Failed to get Redis info: {e}")
                    redis_info = {"error": str(e)}
                
                # Get system metrics
                system_metrics = {
                    "timestamp": datetime.now().isoformat(),
                    "uptime_seconds": None,  # Could add process uptime if needed
                    "memory_usage": None,    # Could add memory usage if needed
                }
                
                return {
                    "redis": redis_info,
                    "system": system_metrics,
                    "services": {
                        "n8n_configured": bool(settings.N8N_API_URL and settings.N8N_API_KEY),
                        "ai_configured": bool(settings.GEMINI_API_KEY or settings.OPENAI_API_KEY),
                    }
                }
            except Exception as e:
                logger.error(f"Failed to get service metrics: {e}")
                return {"error": str(e)}
        
        return await self.execute_operation(_get_service_metrics, context)


# Global service instance
health_service = HealthService()