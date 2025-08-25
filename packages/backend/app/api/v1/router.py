"""Main API router"""

from fastapi import APIRouter

from app.api.v1.endpoints import health, chat, metrics, config

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
api_router.include_router(config.router, prefix="/config", tags=["config"])