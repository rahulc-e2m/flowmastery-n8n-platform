"""FastAPI application entry point"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.api.v1.router import api_router
from app.core.middleware import setup_middleware
from app.core.exceptions import setup_exception_handlers
from app.utils.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    setup_logging()
    
    # Initialize services
    from app.services.cache.redis import redis_client
    from app.services.n8n.client import n8n_client
    
    try:
        # Test Redis connection
        await redis_client.ping()
        print("✅ Redis connection established")
    except Exception as e:
        print(f"⚠️  Redis connection failed: {e}")
    
    # Test n8n connection if configured
    if settings.N8N_API_URL and settings.N8N_API_KEY:
        try:
            health = await n8n_client.health_check()
            if health:
                print("✅ n8n connection established")
            else:
                print("⚠️  n8n connection failed")
        except Exception as e:
            print(f"⚠️  n8n connection error: {e}")
    
    yield
    
    # Shutdown
    try:
        await redis_client.close()
        print("✅ Redis connection closed")
    except Exception as e:
        print(f"⚠️  Redis shutdown error: {e}")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Modern backend API for FlowMastery with n8n integration",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan
    )
    
    # Setup CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_cors_origins_list(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Setup trusted hosts
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure properly in production
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
        return {
            "message": f"{settings.APP_NAME} API",
            "version": settings.APP_VERSION,
            "status": "running",
            "docs": "/docs" if settings.DEBUG else "disabled"
        }
    
    @app.get("/health")
    async def health():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "version": settings.APP_VERSION
        }
    
    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"📡 Debug mode: {settings.DEBUG}")
    print(f"🔗 n8n Integration: {'✅' if settings.N8N_API_URL else '❌'}")
    print(f"🤖 AI Services: {'✅' if settings.GEMINI_API_KEY else '❌'}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )