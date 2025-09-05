"""Consolidated automation endpoints - chatbots and chat operations"""

import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter

from app.database import get_db
from app.models.user import User
from app.schemas.chatbot import (
    ChatbotCreate,
    ChatbotUpdate,
    ChatbotResponse,
    ChatbotListResponse
)
from app.schemas.chat import ChatMessage, ChatResponse, ChatHistoryResponse, ConversationListResponse, ChatTestResponse
from app.schemas.responses import (
    ChatbotCreatedResponse,
    ChatbotUpdatedResponse,
    ChatbotDeletedResponse,
    ChatbotListResponse as StandardChatbotListResponse
)
from app.services.chatbot_service import ChatbotService
from app.services.chat_service import ChatService
from app.core.dependencies import get_current_user
from app.core.user_roles import UserRole, RolePermissions
from app.core.role_based_filter import RoleBasedDataFilter
from app.core.decorators import validate_input, sanitize_response
from app.core.response_formatter import format_response
from app.core.rate_limiting import get_user_identifier, RATE_LIMITS
from app.services.cache.redis import redis_client

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_user_identifier)


class ChatbotServiceMixin:
    """Service layer mixin for chatbot operations"""
    
    @staticmethod
    async def _check_chatbot_rate_limit(user_id: str, operation: str, limit: int = 30, window: int = 60) -> bool:
        """Check rate limit for chatbot operations"""
        try:
            current_time = int(datetime.utcnow().timestamp())
            window_start = current_time - window
            rate_limit_key = f"rate_limit:chatbots:{operation}:{user_id}"
            
            pipe = redis_client.pipeline()
            pipe.zremrangebyscore(rate_limit_key, 0, window_start)
            pipe.zcard(rate_limit_key)
            pipe.zadd(rate_limit_key, {str(current_time): current_time})
            pipe.expire(rate_limit_key, window)
            
            results = await pipe.execute()
            current_requests = results[1]
            
            return current_requests < limit
        except Exception as e:
            logger.warning(f"Chatbot rate limiter error: {e}")
            return True  # Fail open
    
    @staticmethod
    async def _get_chatbot_cache(key: str) -> Optional[dict]:
        """Get chatbot data from cache"""
        try:
            value = await redis_client.get(f"chatbot_cache:{key}")
            if value:
                import json
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Chatbot cache get error: {e}")
            return None
    
    @staticmethod
    async def _set_chatbot_cache(key: str, value: dict, ttl: int = 300) -> bool:
        """Set chatbot data in cache"""
        try:
            import json
            serialized_value = json.dumps(value, default=str)
            await redis_client.setex(f"chatbot_cache:{key}", ttl, serialized_value)
            return True
        except Exception as e:
            logger.warning(f"Chatbot cache set error: {e}")
            return False
    
    @staticmethod
    async def _invalidate_chatbot_cache(pattern: str) -> bool:
        """Invalidate chatbot cache entries"""
        try:
            keys = await redis_client.keys(f"chatbot_cache:{pattern}")
            if keys:
                await redis_client.delete(*keys)
            return True
        except Exception as e:
            logger.warning(f"Chatbot cache invalidation error: {e}")
            return False


# Chatbot Management Endpoints

@router.get("/chatbots")
@format_response(message="Chatbots retrieved successfully")
async def get_chatbots(
    client_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleBasedDataFilter.get_admin_or_client_user())
):
    """Get chatbots - replaces /chatbots/ + /chatbots/my with role-based filtering"""
    
    # Rate limiting
    if not await ChatbotServiceMixin._check_chatbot_rate_limit(current_user.id, "list"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    
    if RolePermissions.is_admin(current_user.role):
        if client_id:
            # Admin requesting specific client's chatbots
            # Verify client exists
            accessible_client_ids = await RoleBasedDataFilter.get_accessible_client_ids(
                current_user, db, client_id
            )
            if client_id not in accessible_client_ids:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Client not found"
                )
            
            # Try cache first
            cache_key = f"client_chatbots:{client_id}"
            cached_result = await ChatbotServiceMixin._get_chatbot_cache(cache_key)
            if cached_result:
                return ChatbotListResponse(**cached_result)
            
            # Get chatbots for specific client
            result = await ChatbotService.get_client_chatbots(db, client_id)
            
            # Cache the result
            result_dict = result.model_dump() if hasattr(result, 'model_dump') else result.__dict__
            await ChatbotServiceMixin._set_chatbot_cache(cache_key, result_dict, ttl=180)
            
            return result
        else:
            # Admin requesting all chatbots
            cache_key = "all_chatbots"
            cached_result = await ChatbotServiceMixin._get_chatbot_cache(cache_key)
            if cached_result:
                return ChatbotListResponse(**cached_result)
            
            result = await ChatbotService.get_all_chatbots(db)
            
            # Cache the result
            result_dict = result.model_dump() if hasattr(result, 'model_dump') else result.__dict__
            await ChatbotServiceMixin._set_chatbot_cache(cache_key, result_dict, ttl=180)
            
            return result
    
    elif RolePermissions.is_client(current_user.role):
        # Client requesting their own chatbots
        if client_id and client_id != current_user.client_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this client's chatbots"
            )
        
        result = await ChatbotService.get_user_chatbots(db, current_user)
        return result
    
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid role"
        )


@router.post("/chatbots", response_model=ChatbotCreatedResponse, status_code=status.HTTP_201_CREATED)
@validate_input(max_string_length=2000, allow_html_fields=["description"])
@sanitize_response()
@format_response(
    message="Chatbot created successfully",
    response_model=ChatbotCreatedResponse,
    status_code=201
)
async def create_chatbot(
    chatbot_data: ChatbotCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleBasedDataFilter.get_admin_or_client_user())
):
    """Create a new chatbot"""
    
    # Rate limiting for creation (lower limit)
    if not await ChatbotServiceMixin._check_chatbot_rate_limit(current_user.id, "create", limit=5, window=300):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded for chatbot creation"
        )
    
    try:
        result = await ChatbotService.create_chatbot(db, chatbot_data, current_user)
        
        # Invalidate relevant caches
        await ChatbotServiceMixin._invalidate_chatbot_cache("all_chatbots")
        await ChatbotServiceMixin._invalidate_chatbot_cache(f"user_chatbots:{current_user.id}")
        if current_user.client_id:
            await ChatbotServiceMixin._invalidate_chatbot_cache(f"client_chatbots:{current_user.client_id}")
        
        logger.info(f"Created chatbot {result.id} by user {current_user.id}")
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating chatbot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create chatbot"
        )


@router.get("/chatbots/{chatbot_id}", response_model=ChatbotResponse)
@format_response(message="Chatbot retrieved successfully")
async def get_chatbot(
    chatbot_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleBasedDataFilter.get_admin_or_client_user())
):
    """Get a specific chatbot by ID"""
    
    # Verify chatbot access
    if not await RoleBasedDataFilter.verify_resource_access(
        current_user, "chatbot", chatbot_id, db
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this chatbot"
        )
    
    chatbot = await ChatbotService.get_chatbot_by_id(db, chatbot_id, current_user)
    if not chatbot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatbot not found"
        )
    return chatbot


@router.patch("/chatbots/{chatbot_id}", response_model=ChatbotUpdatedResponse)
@validate_input(max_string_length=2000, allow_html_fields=["description"])
@sanitize_response()
@format_response(
    message="Chatbot updated successfully",
    response_model=ChatbotUpdatedResponse
)
async def update_chatbot(
    chatbot_id: str,
    chatbot_data: ChatbotUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleBasedDataFilter.get_admin_or_client_user())
):
    """Update an existing chatbot"""
    
    # Verify chatbot access
    if not await RoleBasedDataFilter.verify_resource_access(
        current_user, "chatbot", chatbot_id, db
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this chatbot"
        )
    
    try:
        chatbot = await ChatbotService.update_chatbot(db, chatbot_id, chatbot_data, current_user)
        if not chatbot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chatbot not found"
            )
        
        # Invalidate relevant caches
        await ChatbotServiceMixin._invalidate_chatbot_cache("all_chatbots")
        if current_user.client_id:
            await ChatbotServiceMixin._invalidate_chatbot_cache(f"client_chatbots:{current_user.client_id}")
        
        return chatbot
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/chatbots/{chatbot_id}", status_code=status.HTTP_204_NO_CONTENT)
@format_response(
    message="Chatbot deleted successfully",
    status_code=204
)
async def delete_chatbot(
    chatbot_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleBasedDataFilter.get_admin_or_client_user())
):
    """Delete a chatbot"""
    
    # Verify chatbot access
    if not await RoleBasedDataFilter.verify_resource_access(
        current_user, "chatbot", chatbot_id, db
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this chatbot"
        )
    
    success = await ChatbotService.delete_chatbot(db, chatbot_id, current_user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatbot not found"
        )
    
    # Invalidate relevant caches
    await ChatbotServiceMixin._invalidate_chatbot_cache("all_chatbots")
    if current_user.client_id:
        await ChatbotServiceMixin._invalidate_chatbot_cache(f"client_chatbots:{current_user.client_id}")
    
    return None


# Chat Operations Endpoints

@router.post("/chat", response_model=ChatResponse)
@limiter.limit(RATE_LIMITS["chat"])
@validate_input(max_string_length=5000, sanitize_strings=True)
@sanitize_response()
@format_response(message="Chat message sent successfully")
async def send_chat_message(
    request: Request, 
    chat_message: ChatMessage,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user())
):
    """Send message to chatbot - any authenticated user can chat"""
    
    chat_service = ChatService(db)
    return await chat_service.process_chat_message(chat_message)


@router.get("/chat/{chatbot_id}/history")
@format_response(message="Chat history retrieved successfully")
async def get_chat_history(
    chatbot_id: str,
    conversation_id: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleBasedDataFilter.get_admin_or_client_user())
) -> Dict[str, Any]:
    """Get chat history for a chatbot"""
    
    # Verify chatbot access
    if not await RoleBasedDataFilter.verify_resource_access(
        current_user, "chatbot", chatbot_id, db
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this chatbot"
        )
    
    chat_service = ChatService(db)
    history = await chat_service.get_chat_history(chatbot_id, conversation_id, limit)
    
    return ChatHistoryResponse(
        messages=history.get("messages", []),
        total=history.get("total", 0),
        chatbot_id=chatbot_id,
        conversation_id=conversation_id
    )


@router.get("/chat/{chatbot_id}/conversations")
@format_response(message="Conversation list retrieved successfully")
async def get_conversations(
    chatbot_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleBasedDataFilter.get_admin_or_client_user())
) -> Dict[str, Any]:
    """Get list of conversations for a chatbot"""
    
    # Verify chatbot access
    if not await RoleBasedDataFilter.verify_resource_access(
        current_user, "chatbot", chatbot_id, db
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this chatbot"
        )
    
    chat_service = ChatService(db)
    conversations = await chat_service.get_conversation_list(chatbot_id)
    
    return ConversationListResponse(
        conversations=conversations,
        total=len(conversations),
        chatbot_id=chatbot_id
    )


@router.get("/chat/test")
@format_response(message="Chat service status retrieved successfully")
async def test_chat() -> Dict[str, Any]:
    """Test chat functionality"""
    return ChatTestResponse(
        status="ok",
        message="Chat service is running with service layer",
        timestamp=datetime.now().isoformat()
    )