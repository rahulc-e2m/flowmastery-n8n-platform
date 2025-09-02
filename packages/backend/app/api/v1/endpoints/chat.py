"""Chat endpoints - Using service layer"""

from datetime import datetime
from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from slowapi import Limiter

from app.database import get_db
from app.schemas.chat import ChatMessage, ChatResponse
from app.services.chat_service import ChatService
from app.core.rate_limiting import get_user_identifier, RATE_LIMITS
from app.core.decorators import validate_input, sanitize_response

router = APIRouter()

# Initialize rate limiter
limiter = Limiter(key_func=get_user_identifier)


@router.post("/", response_model=ChatResponse)
@limiter.limit(RATE_LIMITS["chat"])
@validate_input(max_string_length=5000, sanitize_strings=True)
@sanitize_response()
async def chat_endpoint(
    request: Request, 
    chat_message: ChatMessage,
    db: AsyncSession = Depends(get_db)
) -> ChatResponse:
    """Send message to chatbot webhook URL using service layer"""
    
    chat_service = ChatService(db)
    return await chat_service.process_chat_message(chat_message)


@router.get("/{chatbot_id}/history")
async def get_chat_history(
    chatbot_id: str,
    conversation_id: str = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get chat history for a chatbot using service layer"""
    
    chat_service = ChatService(db)
    return await chat_service.get_chat_history(chatbot_id, conversation_id, limit)


@router.get("/{chatbot_id}/conversations")
async def get_conversations(
    chatbot_id: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get list of conversations for a chatbot"""
    
    chat_service = ChatService(db)
    conversations = await chat_service.get_conversation_list(chatbot_id)
    
    return {
        "conversations": conversations,
        "total": len(conversations)
    }


@router.get("/test")
async def test_chat() -> Dict[str, Any]:
    """Test chat functionality"""
    return {
        "status": "ok",
        "message": "Chat service is running with service layer",
        "timestamp": datetime.now().isoformat()
    }