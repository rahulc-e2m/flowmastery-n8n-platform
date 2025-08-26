"""n8n integration services"""

from .client import n8n_client
# from .chatbot import ChatbotService  # Import only when needed to avoid Google AI dependencies
from .metrics import MetricsService
from .config import ConfigService

__all__ = ["n8n_client", "MetricsService", "ConfigService"]

# Lazy import for chatbot to avoid loading Google AI dependencies unless needed
def get_chatbot_service():
    from .chatbot import ChatbotService
    return ChatbotService