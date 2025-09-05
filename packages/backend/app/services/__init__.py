"""
Services package initialization - Register all services with the service layer
"""

from app.core.service_layer import register_service

# Import all services
from app.services.auth_service import AuthService
from app.services.client_service import ClientService
from app.services.chatbot_service import ChatbotService
from app.services.chat_service import ChatService
from app.services.guide_service import GuideService
from app.services.metrics_service import metrics_service
from app.services.workflow_service import workflow_service
from app.services.health_service import health_service
from app.services.config_service import config_service

# Register services in the global registry
def initialize_services():
    """Initialize and register all services"""
    register_service("auth_service", AuthService())
    register_service("client_service", ClientService())
    register_service("chatbot_service", ChatbotService())
    register_service("guide_service", GuideService(None))  # DB will be injected
    register_service("metrics_service", metrics_service)
    register_service("workflow_service", workflow_service)
    register_service("health_service", health_service)
    register_service("config_service", config_service)

# Auto-initialize when imported
initialize_services()

__all__ = [
    "AuthService",
    "ClientService", 
    "ChatbotService",
    "ChatService",
    "GuideService",
    "metrics_service",
    "workflow_service",
    "health_service",
    "config_service",
    "initialize_services"
]