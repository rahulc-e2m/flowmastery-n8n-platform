"""Chat service layer for handling chat operations"""

import httpx
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models import Chatbot, ChatMessage as ChatMessageModel
from app.schemas.chat import ChatMessage, ChatResponse

logger = logging.getLogger(__name__)


class ChatService:
    """Service class for handling chat operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_chatbot(self, chatbot_id: str) -> Chatbot:
        """Get chatbot by ID with validation"""
        stmt = select(Chatbot).where(Chatbot.id == chatbot_id)
        result = await self.db.execute(stmt)
        chatbot = result.scalars().first()
        
        if not chatbot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chatbot not found"
            )
        
        if not chatbot.webhook_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Chatbot webhook URL not configured"
            )
        
        if not chatbot.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Chatbot is not active"
            )
        
        return chatbot
    
    async def send_webhook_message(
        self, 
        webhook_url: str, 
        message: str, 
        conversation_id: str, 
        message_id: str
    ) -> Dict[str, Any]:
        """Send message to webhook and return response"""
        webhook_payload = {
            "message": message,
            "sessionId": conversation_id,
            "message_id": message_id,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Sending message to webhook: {webhook_url[:50]}...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    webhook_url,
                    json=webhook_payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code != 200:
                    logger.error(f"Webhook returned status {response.status_code}: {response.text}")
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"Webhook returned status {response.status_code}"
                    )
                
                webhook_response = response.json()
                logger.info(f"Webhook response received: {webhook_response}")
                return webhook_response
        
        except httpx.TimeoutException:
            logger.error(f"Webhook request timed out for URL: {webhook_url}")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Webhook request timed out"
            )
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to webhook {webhook_url}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to connect to webhook: {str(e)}"
            )
    
    def extract_bot_response(self, webhook_response: Dict[str, Any]) -> str:
        """Extract bot response from webhook response"""
        # Try multiple possible field names that n8n might use
        return (
            webhook_response.get("response") or 
            webhook_response.get("message") or 
            webhook_response.get("text") or 
            webhook_response.get("output") or 
            webhook_response.get("reply") or
            "I received your message."
        )
    
    async def save_chat_message(
        self,
        message_id: str,
        chatbot_id: str,
        conversation_id: str,
        user_message: str,
        bot_response: str,
        processing_time: float,
        source: str = "webhook"
    ) -> ChatMessageModel:
        """Save chat message to database"""
        try:
            chat_message_record = ChatMessageModel(
                id=message_id,
                chatbot_id=chatbot_id,
                conversation_id=conversation_id,
                user_message=user_message,
                bot_response=bot_response,
                processing_time=processing_time,
                source=source,
                timestamp=datetime.now()
            )
            
            self.db.add(chat_message_record)
            await self.db.commit()
            await self.db.refresh(chat_message_record)
            
            logger.info(f"Chat message saved: {message_id}")
            return chat_message_record
        
        except Exception as e:
            logger.error(f"Failed to save chat message {message_id}: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save chat message"
            )
    
    async def process_chat_message(self, chat_message: ChatMessage) -> ChatResponse:
        """Process a chat message through the complete flow"""
        start_time = datetime.now()
        message_id = str(uuid.uuid4())
        
        try:
            # Validate chatbot_id
            if not chat_message.chatbot_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="chatbot_id is required"
                )
            
            # Get and validate chatbot
            chatbot = await self.get_chatbot(chat_message.chatbot_id)
            
            # Generate conversation ID if not provided
            conversation_id = chat_message.conversation_id or str(uuid.uuid4())
            
            # Send message to webhook
            webhook_response = await self.send_webhook_message(
                chatbot.webhook_url,
                chat_message.message,
                conversation_id,
                message_id
            )
            
            # Extract bot response
            bot_response = self.extract_bot_response(webhook_response)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Save to database
            await self.save_chat_message(
                message_id=message_id,
                chatbot_id=chat_message.chatbot_id,
                conversation_id=conversation_id,
                user_message=chat_message.message,
                bot_response=bot_response,
                processing_time=processing_time,
                source="webhook"
            )
            
            return ChatResponse(
                response=bot_response,
                message_id=message_id,
                timestamp=datetime.now(),
                chatbot_id=chat_message.chatbot_id,
                conversation_id=conversation_id
            )
        
        except Exception as e:
            # Handle errors gracefully
            processing_time = (datetime.now() - start_time).total_seconds()
            conversation_id = chat_message.conversation_id or str(uuid.uuid4())
            
            # If it's not an HTTPException, create a generic error response
            if not isinstance(e, HTTPException):
                return ChatResponse(
                    response="Sorry, I encountered an error processing your message. Please try again.",
                    message_id=message_id,
                    timestamp=datetime.now(),
                    chatbot_id=chat_message.chatbot_id,
                    conversation_id=conversation_id
                )
            else:
                # Re-raise HTTPExceptions
                raise e
    
    async def get_chat_history(
        self,
        chatbot_id: str,
        conversation_id: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get chat history for a chatbot"""
        
        # Validate that chatbot exists
        await self.get_chatbot(chatbot_id)
        
        query = select(ChatMessageModel).where(ChatMessageModel.chatbot_id == chatbot_id)
        
        if conversation_id:
            query = query.where(ChatMessageModel.conversation_id == conversation_id)
        
        query = query.order_by(ChatMessageModel.timestamp.desc()).limit(limit)
        
        result = await self.db.execute(query)
        messages = result.scalars().all()
        
        return {
            "messages": [
                {
                    "id": msg.id,
                    "conversation_id": msg.conversation_id,
                    "user_message": msg.user_message,
                    "bot_response": msg.bot_response,
                    "timestamp": msg.timestamp.isoformat(),
                    "processing_time": msg.processing_time,
                    "source": msg.source
                }
                for msg in messages
            ],
            "total": len(messages)
        }
    
    async def get_conversation_list(self, chatbot_id: str) -> List[Dict[str, Any]]:
        """Get list of conversations for a chatbot"""
        
        # Validate that chatbot exists
        await self.get_chatbot(chatbot_id)
        
        # Get all messages for this chatbot, ordered by timestamp desc
        query = select(ChatMessageModel).where(
            ChatMessageModel.chatbot_id == chatbot_id
        ).order_by(ChatMessageModel.timestamp.desc())
        
        result = await self.db.execute(query)
        all_messages = result.scalars().all()
        
        # Group by conversation_id and get the latest message for each
        conversations_dict = {}
        for msg in all_messages:
            if msg.conversation_id not in conversations_dict:
                conversations_dict[msg.conversation_id] = {
                    "conversation_id": msg.conversation_id,
                    "last_message_time": msg.timestamp.isoformat(),
                    "last_user_message": msg.user_message[:100] + "..." if len(msg.user_message) > 100 else msg.user_message
                }
        
        # Convert to list and sort by timestamp (most recent first)
        conversations_list = list(conversations_dict.values())
        conversations_list.sort(key=lambda x: x["last_message_time"], reverse=True)
        
        return conversations_list