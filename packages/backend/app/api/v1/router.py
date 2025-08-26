"""Main API router"""

from fastapi import APIRouter

from app.api.v1.endpoints import health, chat, metrics, config, auth, clients, cache, tasks

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(config.router, prefix="/config", tags=["config"])
api_router.include_router(cache.router, prefix="/cache", tags=["cache"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])