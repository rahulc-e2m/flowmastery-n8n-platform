"""
Chat Service - Manages chat operations with service layer protection
"""

import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from app.core.service_layer import BaseService, OperationContext, OperationType, OperationResult
from app.schemas.chat import ChatMessage, ChatResponse
from app.config import settings

logger = logging.getLogger(__name__)


class ChatService(BaseService[Dict[str, Any]]):
    """Service for managing chat operations with full service layer protection"""
    
    @property
    def service_name(self) -> str:
        return "chat_service"
    
    async def process_chat_message(
        self, 
        message: str, 
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> OperationResult[ChatResponse]:
        """Process a chat message with service layer protection"""
        context = OperationContext(
            operation_type=OperationType.CREATE,
            user_id=user_id,
            metadata={
                "message_length": len(message),
                "conversation_id": conversation_id
            }
        )
        
        # Input validation
        await self._validate_input(message, context)
        
        async def _process_message():
            start_time = datetime.now()
            
            try:
                # Import here to avoid circular imports
                from app.services.n8n.chatbot import chatbot_service
                
                # Process message with integrated chatbot service
                result = await chatbot_service.process_message(
                    message=message,
                    conversation_id=conversation_id
                )
                
                processing_time = (datetime.now() - start_time).total_seconds()
                
                return ChatResponse(
                    response=result["response"],
                    message_id=result["message_id"],
                    timestamp=result["timestamp"],
                    processing_time=processing_time,
                    source=result["source"],
                    conversation_id=result.get("conversation_id")
                )
                
            except Exception as e:
                logger.error(f"Chat processing error: {e}")
                processing_time = (datetime.now() - start_time).total_seconds()
                
                # Fallback error response
                message_id = str(uuid.uuid4())
                
                return ChatResponse(
                    response=f"I encountered an error processing your message: {str(e)}",
                    message_id=message_id,
                    timestamp=datetime.now().isoformat(),
                    processing_time=processing_time,
                    source="error",
                    conversation_id=conversation_id
                )
        
        return await self.execute_operation(_process_message, context)
    
    async def get_chat_test_status(self, use_cache: bool = True) -> OperationResult[Dict[str, Any]]:
        """Get chat service test status"""
        context = OperationContext(operation_type=OperationType.READ)
        
        async def _get_test_status():
            # Check cache first
            if use_cache:
                cache_key = "chat_test_status"
                cached_result = await self._get_from_cache(cache_key)
                if cached_result:
                    return cached_result
            
            result = {
                "status": "ok",
                "message": "Chat service is running",
                "timestamp": datetime.now().isoformat(),
                "configuration": {
                    "n8n_configured": bool(settings.N8N_API_URL and settings.N8N_API_KEY),
                    "ai_configured": bool(settings.GEMINI_API_KEY),
                    "n8n_url": settings.N8N_API_URL if settings.N8N_API_URL else "Not configured"
                },
                "service_health": await self._check_chat_service_health()
            }
            
            # Cache for 60 seconds
            if use_cache:
                await self._set_cache("chat_test_status", result, ttl=60)
            
            return result
        
        return await self.execute_operation(_get_test_status, context)
    
    async def _validate_input(self, message: str, context: OperationContext) -> None:
        """Validate chat message input"""
        if not message or not message.strip():
            raise ValueError("Message cannot be empty")
        
        if len(message) > 5000:  # Max message length
            raise ValueError("Message too long (max 5000 characters)")
        
        # Check for potential abuse patterns
        if message.count('\n') > 50:  # Too many line breaks
            raise ValueError("Message format invalid")
        
        # Basic content filtering (could be expanded)
        forbidden_patterns = ['<script', 'javascript:', 'data:']
        message_lower = message.lower()
        for pattern in forbidden_patterns:
            if pattern in message_lower:
                raise ValueError("Message contains forbidden content")
    
    async def _check_chat_service_health(self) -> Dict[str, Any]:
        """Check chat service dependencies health"""
        health_status = {
            "n8n_service": "unknown",
            "ai_service": "unknown",
            "overall": "unknown"
        }
        
        try:
            # Check n8n service
            if settings.N8N_API_URL and settings.N8N_API_KEY:
                from app.services.n8n.client import n8n_client
                n8n_healthy = await n8n_client.health_check()
                health_status["n8n_service"] = "healthy" if n8n_healthy else "unhealthy"
            else:
                health_status["n8n_service"] = "not_configured"
            
            # Check AI service configuration
            if settings.GEMINI_API_KEY or settings.OPENAI_API_KEY:
                health_status["ai_service"] = "configured"
            else:
                health_status["ai_service"] = "not_configured"
            
            # Determine overall health
            if (health_status["n8n_service"] in ["healthy", "not_configured"] and 
                health_status["ai_service"] in ["configured", "not_configured"]):
                health_status["overall"] = "healthy"
            else:
                health_status["overall"] = "degraded"
                
        except Exception as e:
            logger.warning(f"Chat service health check error: {e}")
            health_status["overall"] = "error"
            health_status["error"] = str(e)
        
        return health_status
    
    async def get_conversation_history(
        self, 
        conversation_id: str, 
        limit: int = 50,
        user_id: Optional[str] = None
    ) -> OperationResult[Dict[str, Any]]:
        """Get conversation history (placeholder for future implementation)"""
        context = OperationContext(
            operation_type=OperationType.READ,
            user_id=user_id,
            metadata={"conversation_id": conversation_id, "limit": limit}
        )
        
        async def _get_history():
            # Placeholder implementation
            # In a real implementation, this would fetch from a database
            return {
                "conversation_id": conversation_id,
                "messages": [],
                "total_messages": 0,
                "message": "Conversation history not yet implemented"
            }
        
        return await self.execute_operation(_get_history, context)
    
    async def clear_conversation(
        self, 
        conversation_id: str,
        user_id: Optional[str] = None
    ) -> OperationResult[Dict[str, Any]]:
        """Clear conversation history (placeholder for future implementation)"""
        context = OperationContext(
            operation_type=OperationType.DELETE,
            user_id=user_id,
            metadata={"conversation_id": conversation_id}
        )
        
        async def _clear_conversation():
            # Placeholder implementation
            # In a real implementation, this would clear from database
            return {
                "conversation_id": conversation_id,
                "cleared": True,
                "message": "Conversation clearing not yet implemented"
            }
        
        return await self.execute_operation(_clear_conversation, context)


# Global service instance
chat_service = ChatService()