"""Chat endpoints"""

from fastapi import APIRouter, HTTPException, Request, status
from typing import Dict, Any
from slowapi import Limiter

from app.schemas.chat import ChatMessage, ChatResponse
from app.services.chat_service import chat_service
from app.core.rate_limiting import get_user_identifier, RATE_LIMITS
from app.core.decorators import validate_input, sanitize_response

router = APIRouter()

# Initialize rate limiter
limiter = Limiter(key_func=get_user_identifier)


@router.post("/", response_model=ChatResponse)
@limiter.limit(RATE_LIMITS["chat"])
@validate_input(max_string_length=5000, sanitize_strings=True)
@sanitize_response()
async def chat_endpoint(request: Request, chat_message: ChatMessage) -> ChatResponse:
    """Main chat endpoint with integrated chatbot service"""
    
    # Get user identifier for service layer context
    user_identifier = get_user_identifier(request)
    
    result = await chat_service.process_chat_message(
        message=chat_message.message,
        conversation_id=chat_message.conversation_id,
        user_id=user_identifier
    )
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error
        )
    
    return result.data


@router.get("/test")
async def test_chat() -> Dict[str, Any]:
    """Test chat functionality"""
    result = await chat_service.get_chat_test_status()
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error
        )
    
    return result.data