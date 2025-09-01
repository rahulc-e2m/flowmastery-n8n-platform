"""Chatbot endpoints"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....database.connection import get_db
from ....models import User
from ....schemas.chatbot import (
    ChatbotCreate,
    ChatbotUpdate,
    ChatbotResponse,
    ChatbotListResponse
)
from ....services.chatbot_service import ChatbotService
from ..dependencies import get_current_user, require_admin
from ....core.decorators import validate_input, sanitize_response

router = APIRouter()


@router.get("/", response_model=ChatbotListResponse)
async def get_all_chatbots(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get all chatbots (admin only)"""
    return await ChatbotService.get_all_chatbots(db)


@router.get("/my", response_model=ChatbotListResponse)
async def get_my_chatbots(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get chatbots for the current user's client"""
    return await ChatbotService.get_user_chatbots(db, current_user)


@router.get("/{chatbot_id}", response_model=ChatbotResponse)
async def get_chatbot(
    chatbot_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific chatbot by ID"""
    chatbot = await ChatbotService.get_chatbot_by_id(db, chatbot_id, current_user)
    if not chatbot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatbot not found"
        )
    return chatbot


@router.post("/", response_model=ChatbotResponse, status_code=status.HTTP_201_CREATED)
@validate_input(max_string_length=2000, allow_html_fields=["description"])
@sanitize_response()
async def create_chatbot(
    chatbot_data: ChatbotCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new chatbot"""
    try:
        return await ChatbotService.create_chatbot(db, chatbot_data, current_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/{chatbot_id}", response_model=ChatbotResponse)
@validate_input(max_string_length=2000, allow_html_fields=["description"])
@sanitize_response()
async def update_chatbot(
    chatbot_id: str,
    chatbot_data: ChatbotUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
async def delete_chatbot(
    chatbot_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a chatbot"""
    success = await ChatbotService.delete_chatbot(db, chatbot_id, current_user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatbot not found"
        )