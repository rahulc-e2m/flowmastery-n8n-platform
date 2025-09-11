"""FastAPI application entry point"""

import logging
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

logger = logging.getLogger(__name__)

from app.config import settings
from app.api.v1.router import api_router
from app.core.middleware import setup_middleware
from app.core.exceptions import setup_exception_handlers
from app.utils.logging import setup_logging


# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    setup_logging()
    
    # Log security configuration
    allowed_hosts = settings.get_allowed_hosts_list()
    cors_methods = settings.get_cors_methods_list()
    cors_headers = settings.get_cors_headers_list()
    
    is_production = settings.ENVIRONMENT.lower() == "production"
    
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"🌍 Environment: {settings.ENVIRONMENT}")
    print(f"📡 Debug mode: {settings.DEBUG}")
    print(f"📚 API Docs: {'disabled (production)' if is_production else 'enabled (/docs)'}")
    print(f"🛡️  Allowed hosts: {', '.join(allowed_hosts)}")
    print(f"🌐 CORS methods: {', '.join(cors_methods)}")
    print(f"📋 CORS headers: {len(cors_headers)} headers configured")
    
    # Initialize database
    from app.database import engine
    from app.database.base import Base
    
    try:
        # Test database connection
        async with engine.begin() as conn:
            # Note: Database tables should be created via Alembic migrations
            # Run manually: docker-compose exec backend alembic upgrade head
            pass
        print("✅ Database connection established")
    except Exception as e:
        print(f"⚠️  Database connection failed: {e}")
    
    # Initialize services
    try:
        from app.services.cache.redis import redis_client
        # Test Redis connection
        await redis_client.ping()
        print("✅ Redis connection established")
    except Exception as e:
        print(f"⚠️  Redis connection failed: {e}")
    
    # Initialize service layer
    try:
        from app.services import initialize_services
        initialize_services()
        print("✅ Service layer initialized")
    except Exception as e:
        print(f"⚠️  Service layer initialization failed: {e}")
    
    # Note: Celery workers are started separately via docker-compose
    print("✅ Application startup complete")
    
    yield
    
    # Shutdown
    try:
        from app.services.cache.redis import redis_client
        await redis_client.close()
        print("✅ Redis connection closed")
    except Exception as e:
        print(f"⚠️  Redis shutdown error: {e}")
    
    try:
        await engine.dispose()
        print("✅ Database connection closed")
    except Exception as e:
        print(f"⚠️  Database shutdown error: {e}")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    # Disable API documentation in production for security
    is_production = settings.ENVIRONMENT.lower() == "production"
    docs_url = None if is_production else "/docs"
    redoc_url = None if is_production else "/redoc"
    
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Modern backend API for FlowMastery with n8n integration",
        docs_url=docs_url,
        redoc_url=redoc_url,
        lifespan=lifespan
    )
    
    # Add rate limiter state and exception handler
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # Setup CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_cors_origins_list(),
        allow_credentials=True,
        allow_methods=settings.get_cors_methods_list(),
        allow_headers=settings.get_cors_headers_list(),
    )
    
    # Add service layer monitoring middleware
    @app.middleware("http")
    async def service_layer_monitoring(request, call_next):
        start_time = datetime.utcnow()
        
        # Add request ID for tracing
        import uuid
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        response = await call_next(request)
        
        # Log slow requests
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        if execution_time > 5.0:  # Log requests taking more than 5 seconds
            logger.warning(
                f"Slow request: {request.method} {request.url.path} "
                f"took {execution_time:.2f}s (request_id: {request_id})"
            )
        
        # Add performance headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{execution_time:.3f}s"
        
        return response
    
    # Add middleware to handle ngrok headers
    @app.middleware("http")
    async def add_ngrok_headers(request, call_next):
        response = await call_next(request)
        # Add ngrok bypass header to response (for CORS)
        response.headers["ngrok-skip-browser-warning"] = "true"
        return response
    
    # Setup trusted hosts
    allowed_hosts = settings.get_allowed_hosts_list()
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=allowed_hosts
    )
    
    # Setup custom middleware
    setup_middleware(app)
    
    # Setup exception handlers
    setup_exception_handlers(app)
    
    # Include API router
    app.include_router(api_router, prefix="/api/v1")
    
    @app.get("/")
    async def root():
        """Root endpoint"""
        is_production = settings.ENVIRONMENT.lower() == "production"
        return {
            "message": f"{settings.APP_NAME} API",
            "version": settings.APP_VERSION,
            "status": "running",
            "environment": settings.ENVIRONMENT,
            "docs": "disabled (production)" if is_production else "/docs"
        }
    
    @app.get("/health")
    async def health():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "version": settings.APP_VERSION
        }
    
    @app.get("/health/service-layer")
    async def service_layer_health():
        """Service layer health check endpoint"""
        try:
            from app.services.cache.redis import redis_client
            
            # Test Redis connection
            redis_healthy = False
            try:
                await redis_client.ping()
                redis_healthy = True
            except Exception as e:
                logger.warning(f"Redis health check failed: {e}")
            
            # Test database connection
            db_healthy = False
            try:
                from app.database import engine
                from sqlalchemy import text
                async with engine.begin() as conn:
                    await conn.execute(text("SELECT 1"))
                db_healthy = True
            except Exception as e:
                logger.warning(f"Database health check failed: {e}")
            
            # Check service layer components
            service_layer_status = {
                "redis_cache": "healthy" if redis_healthy else "unhealthy",
                "database": "healthy" if db_healthy else "unhealthy",
                "rate_limiting": "enabled",
                "circuit_breaker": "enabled",
                "caching": "enabled",
                "monitoring": "enabled"
            }
            
            overall_healthy = redis_healthy and db_healthy
            
            return {
                "status": "healthy" if overall_healthy else "degraded",
                "version": settings.APP_VERSION,
                "service_layer": service_layer_status,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Service layer health check failed: {e}")
            return {
                "status": "unhealthy",
                "version": settings.APP_VERSION,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )