"""Main API router with consolidated endpoints"""

from fastapi import APIRouter

# Import consolidated endpoints
from app.api.v1.endpoints import health, auth, clients, metrics, workflows, config, cache, tasks, dependencies
from app.api.v1.endpoints.automation import router as automation_router
from app.api.v1.endpoints.system import router as system_router

api_router = APIRouter()

# Core endpoints
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# Consolidated endpoints - all functionality moved to these
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["workflows"])
api_router.include_router(automation_router, prefix="/automation", tags=["automation"])
api_router.include_router(system_router, prefix="/system", tags=["system"])

# Remaining endpoints (may be deprecated later)
api_router.include_router(config.router, prefix="/config", tags=["config"])
api_router.include_router(cache.router, prefix="/cache", tags=["cache"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(dependencies.router, prefix="/dependencies", tags=["dependencies"])