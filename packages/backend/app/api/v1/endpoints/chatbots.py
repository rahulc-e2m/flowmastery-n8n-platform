"""Chatbot endpoints with service layer protection"""

import asyncio
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.chatbot import (
    ChatbotCreate,
    ChatbotUpdate,
    ChatbotResponse,
    ChatbotListResponse
)
from app.schemas.responses import (
    ChatbotCreatedResponse,
    ChatbotUpdatedResponse,
    ChatbotDeletedResponse,
    ChatbotListResponse as StandardChatbotListResponse
)
from app.services.chatbot_service import ChatbotService
from app.core.dependencies import get_current_user
from app.core.user_roles import UserRole, RolePermissions
from app.core.decorators import validate_input, sanitize_response
from app.core.response_formatter import format_response
from app.services.cache.redis import redis_client

router = APIRouter()
logger = logging.getLogger(__name__)


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


@router.get("/")
@format_response(
    message="Chatbots retrieved successfully"
)
async def get_all_chatbots(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user(required_roles=[UserRole.ADMIN]))
):
    """Get all chatbots (admin only) with service layer protection"""
    # Rate limiting
    if not await ChatbotServiceMixin._check_chatbot_rate_limit(current_user.id, "list_all"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    
    # Try cache first
    cache_key = "all_chatbots"
    cached_result = await ChatbotServiceMixin._get_chatbot_cache(cache_key)
    if cached_result:
        logger.debug("Cache hit for all chatbots")
        return ChatbotListResponse(**cached_result)
    
    try:
        result = await ChatbotService.get_all_chatbots(db)
        
        # Cache the result
        result_dict = result.model_dump() if hasattr(result, 'model_dump') else result.__dict__
        await ChatbotServiceMixin._set_chatbot_cache(cache_key, result_dict, ttl=180)
        
        # Return the service result directly
        return result
    except Exception as e:
        logger.error(f"Error getting all chatbots: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chatbots"
        )


@router.get("/my")
@format_response(
    message="Your chatbots retrieved successfully"
)
async def get_my_chatbots(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user())
):
    """Get chatbots for the current user's client"""
    result = await ChatbotService.get_user_chatbots(db, current_user)
    return result


@router.get("/{chatbot_id}", response_model=ChatbotResponse)
@format_response(message="Chatbot retrieved successfully")
async def get_chatbot(
    chatbot_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user())
):
    """Get a specific chatbot by ID"""
    chatbot = await ChatbotService.get_chatbot_by_id(db, chatbot_id, current_user)
    if not chatbot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatbot not found"
        )
    return chatbot


@router.post("/", response_model=ChatbotCreatedResponse, status_code=status.HTTP_201_CREATED)
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
    current_user: User = Depends(get_current_user())
):
    """Create a new chatbot with service layer protection"""
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


@router.patch("/{chatbot_id}", response_model=ChatbotUpdatedResponse)
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
    current_user: User = Depends(get_current_user())
):
    """Update an existing chatbot"""
    try:
        chatbot = await ChatbotService.update_chatbot(db, chatbot_id, chatbot_data, current_user)
        if not chatbot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chatbot not found"
            )
        return chatbot
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{chatbot_id}", status_code=status.HTTP_204_NO_CONTENT)
@format_response(
    message="Chatbot deleted successfully",
    status_code=204
)
async def delete_chatbot(
    chatbot_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user())
):
    """Delete a chatbot"""
    success = await ChatbotService.delete_chatbot(db, chatbot_id, current_user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatbot not found"
        )
    
    return None
