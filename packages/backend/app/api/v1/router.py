"""Main API router - Final consolidated structure"""

from fastapi import APIRouter

# Import all endpoint modules
from app.api.v1.endpoints import auth, clients, metrics, workflows, cache, tasks, guides
from app.api.v1.endpoints.chatbots import router as chatbots_router
from app.api.v1.endpoints.system import router as system_router
from app.api.v1.endpoints.vistara_workflows import router as vistara_workflows_router
from app.api.v1.endpoints.vistara_categories import router as vistara_categories_router

api_router = APIRouter()

# Authentication endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# Core business endpoints
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["workflows"])
api_router.include_router(chatbots_router, prefix="/chatbots", tags=["chatbots"])

# System administration endpoints
api_router.include_router(system_router, prefix="/system", tags=["system"])
api_router.include_router(cache.router, prefix="/cache", tags=["cache"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])

# User guidance endpoints
api_router.include_router(guides.router, prefix="/guides", tags=["guides"])

# Vistara endpoints
api_router.include_router(vistara_workflows_router, prefix="/vistara/workflows", tags=["vistara-workflows"])
api_router.include_router(vistara_categories_router, prefix="/vistara/categories", tags=["vistara-categories"])
