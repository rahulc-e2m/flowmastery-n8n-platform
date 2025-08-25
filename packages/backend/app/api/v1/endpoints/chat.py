"""Chat endpoints"""

import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.schemas.chat import ChatMessage, ChatResponse
from app.config import settings

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat_endpoint(chat_message: ChatMessage) -> ChatResponse:
    """Main chat endpoint with integrated chatbot service"""
    
    try:
        # Import here to avoid circular imports
        from app.services.n8n.chatbot import chatbot_service
        
        # Process message with integrated chatbot service
        result = await chatbot_service.process_message(
            message=chat_message.message,
            conversation_id=chat_message.conversation_id
        )
        
        return ChatResponse(
            response=result["response"],
            message_id=result["message_id"],
            timestamp=result["timestamp"],
            processing_time=result["processing_time"],
            source=result["source"],
            conversation_id=result.get("conversation_id")
        )
        
    except Exception as e:
        # Fallback error handling
        message_id = str(uuid.uuid4())
        
        return ChatResponse(
            response=f"I encountered an error processing your message: {str(e)}",
            message_id=message_id,
            timestamp=datetime.now().isoformat(),
            processing_time=0.0,
            source="error",
            conversation_id=chat_message.conversation_id
        )


@router.get("/test")
async def test_chat() -> Dict[str, Any]:
    """Test chat functionality"""
    
    return {
        "status": "ok",
        "message": "Chat service is running",
        "timestamp": datetime.now().isoformat(),
        "configuration": {
            "n8n_configured": bool(settings.N8N_API_URL and settings.N8N_API_KEY),
            "ai_configured": bool(settings.GEMINI_API_KEY),
            "n8n_url": settings.N8N_API_URL if settings.N8N_API_URL else "Not configured"
        }
    }