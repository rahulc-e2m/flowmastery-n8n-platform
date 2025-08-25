"""Integrated n8n chatbot service"""

import json
import re
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

import google.generativeai as genai
from app.config import settings
from app.services.n8n.client import n8n_client
from app.core.exceptions import AIServiceError, N8nAPIError

logger = logging.getLogger(__name__)


class ChatbotService:
    """Enhanced chatbot service with n8n integration"""
    
    def __init__(self):
        self.gemini_model = None
        self._setup_ai_client()
    
    def _setup_ai_client(self):
        """Setup AI client"""
        if settings.GEMINI_API_KEY:
            try:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self.gemini_model = genai.GenerativeModel('gemini-2.5-flash-lite-preview-06-17')
                logger.info("Gemini AI client configured")
            except Exception as e:
                logger.error(f"Failed to setup Gemini client: {e}")
        else:
            logger.warning("GEMINI_API_KEY not configured")
    
    async def process_message(
        self, 
        message: str, 
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process user message and generate response"""
        
        start_time = datetime.now()
        message_id = str(uuid.uuid4())
        
        try:
            # Determine if message is n8n-related
            is_n8n_query = await self._is_n8n_related_query(message)
            
            if is_n8n_query and settings.N8N_API_URL and settings.N8N_API_KEY:
                # Process as n8n query
                response = await self._process_n8n_query(message)
                source = "n8n"
            elif self.gemini_model:
                # Process with AI
                response = await self._process_ai_query(message)
                source = "ai"
            else:
                # Fallback response
                response = await self._generate_fallback_response(message)
                source = "fallback"
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "response": response,
                "message_id": message_id,
                "timestamp": datetime.now().isoformat(),
                "processing_time": processing_time,
                "source": source,
                "conversation_id": conversation_id
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "response": f"I encountered an error processing your message: {str(e)}",
                "message_id": message_id,
                "timestamp": datetime.now().isoformat(),
                "processing_time": processing_time,
                "source": "error",
                "conversation_id": conversation_id
            }
    
    async def _is_n8n_related_query(self, message: str) -> bool:
        """Determine if message is related to n8n functionality"""
        n8n_keywords = [
            'workflow', 'execution', 'node', 'trigger', 'automation',
            'n8n', 'api', 'webhook', 'credential', 'variable', 'project',
            'activate', 'deactivate', 'run', 'execute', 'schedule',
            'user', 'tag', 'audit', 'source control'
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in n8n_keywords)
    
    async def _process_n8n_query(self, message: str) -> str:
        """Process n8n-related query"""
        
        try:
            # Get LLM action
            action = await self._get_llm_action(message)
            
            if not action:
                return "I couldn't understand your n8n request. Please try rephrasing it."
            
            # Execute n8n API call
            result = await n8n_client.request(
                method=action.get("method", "GET"),
                endpoint=action.get("path", "/workflows"),
                params=action.get("params"),
                data=action.get("data")
            )
            
            # Format response for user
            formatted_response = self._format_n8n_response(action.get("path", ""), result)
            
            return formatted_response
            
        except Exception as e:
            logger.error(f"n8n query processing failed: {e}")
            return f"I encountered an error while processing your n8n request: {str(e)}"
    
    async def _process_ai_query(self, message: str) -> str:
        """Process query with AI"""
        
        if not self.gemini_model:
            raise AIServiceError("AI service not available")
        
        try:
            system_prompt = f"""
You are a helpful assistant for FlowMastery, a platform that helps users manage their n8n automation workflows.
You can help with:
- General questions about workflow automation
- n8n best practices
- Troubleshooting automation issues
- Explaining workflow concepts

Current context:
- User has n8n configured: {bool(settings.N8N_API_URL)}
- AI services available: Yes

Provide helpful, concise responses. If the user asks about specific n8n operations, 
suggest they use more specific commands or check their n8n instance directly.
"""
            
            prompt = f"{system_prompt}\n\nUser question: {message}\n\nResponse:"
            
            response = self.gemini_model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"AI query processing failed: {e}")
            raise AIServiceError(f"AI processing failed: {str(e)}")
    
    async def _generate_fallback_response(self, message: str) -> str:
        """Generate fallback response"""
        
        responses = [
            f"I understand you're asking about: '{message}'. I'm a FlowMastery assistant, and I can help with workflow automation and n8n management.",
            f"Thanks for your message: '{message}'. I can assist with n8n workflows, executions, and automation tasks.",
            f"I received your query: '{message}'. For full functionality, please ensure your n8n integration and AI services are properly configured.",
        ]
        
        # Simple response selection
        import hashlib
        hash_obj = hashlib.md5(message.encode())
        response_index = int(hash_obj.hexdigest(), 16) % len(responses)
        
        return responses[response_index]
    
    async def _get_llm_action(self, user_query: str) -> Optional[Dict[str, Any]]:
        """Get API action from LLM"""
        
        if not self.gemini_model:
            return None
        
        system_prompt = """
You are an agent that helps users interact with their n8n instance via the n8n REST API.
Choose the correct method (GET, POST, PATCH, PUT, DELETE), endpoint, and parameters from the n8n API.

Common endpoints:
- GET /workflows - List workflows
- GET /workflows/{id} - Get specific workflow
- POST /workflows/{id}/activate - Activate workflow
- POST /workflows/{id}/deactivate - Deactivate workflow
- GET /executions - List executions
- GET /users - List users
- GET /variables - List variables

Output requirements:
- Output valid JSON only, no commentary.
- JSON keys: "method", "path", "params", "data".
- "path" must be a valid n8n API endpoint.
- Put query parameters in "params" and request body in "data".

Example:
{"method": "GET", "path": "/workflows", "params": {"active": "true"}, "data": null}
"""
        
        try:
            prompt = f"{system_prompt}\n\nUser query: {user_query}\n\nOutput only valid JSON:"
            response = self.gemini_model.generate_content(prompt)
            result = response.text.strip()
            
            # Clean up response
            if result.startswith('```json'):
                result = result[7:]
            if result.endswith('```'):
                result = result[:-3]
            
            action = json.loads(result.strip())
            return self._normalize_action_keys(action)
            
        except Exception as e:
            logger.error(f"LLM action generation failed: {e}")
            return None
    
    def _normalize_action_keys(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize action keys"""
        if "endpoint" in action and "path" not in action:
            action["path"] = action.pop("endpoint")
        if "parameters" in action and "params" not in action:
            action["params"] = action.pop("parameters")
        if "params" not in action:
            action["params"] = {}
        if "data" not in action:
            action["data"] = None
        return action
    
    def _format_n8n_response(self, path: str, response: Any) -> str:
        """Format n8n API response for user"""
        
        if not response:
            return "No results found."
        
        try:
            # Handle different response types
            if isinstance(response, list):
                if len(response) == 0:
                    return "No results found."
                elif len(response) == 1:
                    return f"Found 1 result: {self._format_single_item(response[0])}"
                else:
                    return f"Found {len(response)} results:\n" + "\n".join([
                        f"{i+1}. {self._format_single_item(item)}" 
                        for i, item in enumerate(response[:5])
                    ]) + (f"\n... and {len(response) - 5} more" if len(response) > 5 else "")
            
            elif isinstance(response, dict):
                return self._format_single_item(response)
            
            else:
                return str(response)[:500]
                
        except Exception as e:
            logger.error(f"Response formatting failed: {e}")
            return f"Response received but formatting failed: {str(response)[:200]}"
    
    def _format_single_item(self, item: Dict[str, Any]) -> str:
        """Format single item for display"""
        
        if not isinstance(item, dict):
            return str(item)
        
        # Format based on common n8n object types
        if 'name' in item and 'id' in item:
            active_status = f" (active: {item.get('active', 'unknown')})" if 'active' in item else ""
            return f"{item['name']} (ID: {item['id']}){active_status}"
        
        elif 'email' in item:
            role = item.get('role', {}).get('name', 'unknown') if isinstance(item.get('role'), dict) else 'unknown'
            return f"{item['email']} (Role: {role})"
        
        elif 'status' in item and 'workflowId' in item:
            return f"Execution {item.get('id', 'unknown')} - Status: {item['status']} - Workflow: {item['workflowId']}"
        
        elif 'key' in item and 'value' in item:
            return f"{item['key']} = {item['value']}"
        
        else:
            # Generic formatting
            key_fields = ['name', 'id', 'email', 'status', 'key']
            display_parts = []
            
            for field in key_fields:
                if field in item:
                    display_parts.append(f"{field}: {item[field]}")
            
            return " | ".join(display_parts) if display_parts else str(item)[:100]


# Global service instance
chatbot_service = ChatbotService()