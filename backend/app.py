#!/usr/bin/env python3
"""
FastAPI Backend Server for FlowMastery n8n Integration
Combines the existing n8n chatbot functionality with webhook support for the React frontend
"""

import os
import sys
import json
import time
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uvicorn
import requests

# Add current directory to Python path to import the existing modules
sys.path.append(os.path.dirname(__file__))

# Import metrics and config services
try:
    from n8n_metrics import metrics_service, metrics_cache
    from config_service import config_service
    METRICS_SERVICE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import metrics services: {e}")
    METRICS_SERVICE_AVAILABLE = False

try:
    from n8n_chatbot import answer_user, call_n8n_api, validate_and_normalize_action, get_llm_action
    from config import N8N_API_URL, N8N_API_KEY, GEMINI_API_KEY
    N8N_INTEGRATION_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import n8n integration modules: {e}")
    N8N_INTEGRATION_AVAILABLE = False

# Initialize FastAPI app
app = FastAPI(
    title="FlowMastery Backend API",
    description="Backend API server for FlowMastery with n8n integration",
    version="1.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5176", "http://127.0.0.1:3000", "http://127.0.0.1:5173", "http://127.0.0.1:5176"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class ChatMessage(BaseModel):
    message: str
    chatbot_id: Optional[str] = None
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    message_id: str
    timestamp: str
    processing_time: float
    source: str  # "n8n_api" or "webhook" or "fallback"

class WebhookPayload(BaseModel):
    message: Optional[str] = None
    text: Optional[str] = None
    input: Optional[str] = None
    userMessage: Optional[str] = None
    chat: Optional[str] = None
    user: Optional[str] = None
    chatbot_id: Optional[str] = None
    timestamp: Optional[str] = None

class N8nQuery(BaseModel):
    query: str
    include_raw_response: Optional[bool] = False

class ChatbotConfig(BaseModel):
    name: str
    description: str
    webhook_url: str
    n8n_enabled: Optional[bool] = False
    n8n_api_url: Optional[str] = None
    n8n_api_key: Optional[str] = None

class N8nConfig(BaseModel):
    api_url: str
    api_key: str
    instance_name: Optional[str] = "My n8n Instance"

class MetricsRequest(BaseModel):
    execution_days: Optional[int] = 7

# In-memory storage for demo purposes (in production, use a proper database)
chatbot_configs: Dict[str, Dict] = {}
conversation_history: Dict[str, List[Dict]] = {}

@app.get("/")
async def root():
    return {
        "message": "FlowMastery Backend API",
        "version": "1.0.0",
        "n8n_integration": N8N_INTEGRATION_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "n8n_integration": N8N_INTEGRATION_AVAILABLE
    }
    
    if N8N_INTEGRATION_AVAILABLE:
        # Test n8n connectivity
        try:
            # Simple test call to n8n API
            test_response = call_n8n_api("GET", "/workflows", {"limit": 1})
            health_status["n8n_connection"] = "connected"
        except Exception as e:
            health_status["n8n_connection"] = f"error: {str(e)}"
    
    return health_status

@app.post("/api/chat/message")
async def process_chat_message(message_data: ChatMessage) -> ChatResponse:
    """Process a chat message with intelligent routing between n8n API and fallback responses"""
    start_time = time.time()
    message_id = f"msg_{int(time.time() * 1000)}"
    
    try:
        # Determine if this is an n8n-related query
        is_n8n_query = await _is_n8n_related_query(message_data.message)
        
        if is_n8n_query and N8N_INTEGRATION_AVAILABLE:
            # Route to n8n API integration
            try:
                n8n_response = answer_user(message_data.message)
                processing_time = time.time() - start_time
                
                return ChatResponse(
                    response=n8n_response,
                    message_id=message_id,
                    timestamp=datetime.now().isoformat(),
                    processing_time=processing_time,
                    source="n8n_api"
                )
            except Exception as e:
                print(f"n8n API error: {e}")
                # Fall back to general response
                pass
        
        # Fallback to general chatbot response
        fallback_response = await _generate_fallback_response(message_data.message)
        processing_time = time.time() - start_time
        
        return ChatResponse(
            response=fallback_response,
            message_id=message_id,
            timestamp=datetime.now().isoformat(),
            processing_time=processing_time,
            source="fallback"
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        return ChatResponse(
            response=f"I apologize, but I encountered an error processing your message: {str(e)}",
            message_id=message_id,
            timestamp=datetime.now().isoformat(),
            processing_time=processing_time,
            source="error"
        )

@app.post("/api/n8n/query")
async def direct_n8n_query(query_data: N8nQuery):
    """Direct n8n API query endpoint"""
    if not N8N_INTEGRATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="n8n integration not available")
    
    try:
        start_time = time.time()
        
        # Get the n8n API action from LLM
        action = get_llm_action(query_data.query)
        if not action:
            raise HTTPException(status_code=400, detail="Could not determine n8n API action")
        
        # Validate and normalize the action
        normalized_action, error = validate_and_normalize_action(action)
        if error:
            raise HTTPException(status_code=400, detail=f"Invalid action: {error}")
        
        # Call n8n API
        raw_response = call_n8n_api(
            normalized_action['method'],
            normalized_action['path'],
            normalized_action.get('params'),
            normalized_action.get('data')
        )
        
        processing_time = time.time() - start_time
        
        result = {
            "query": query_data.query,
            "action": normalized_action,
            "response": raw_response,
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat()
        }
        
        if not query_data.include_raw_response:
            # Format the response for user-friendly display
            from n8n_chatbot import format_api_result_for_user
            formatted_response = format_api_result_for_user(normalized_action['path'], raw_response)
            result["formatted_response"] = formatted_response
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/webhook/{chatbot_id}")
async def webhook_endpoint(chatbot_id: str, payload: WebhookPayload):
    """Generic webhook endpoint for external chatbot integrations"""
    try:
        # Extract message from various possible fields
        message = (
            payload.message or 
            payload.text or 
            payload.input or 
            payload.userMessage or 
            payload.chat or 
            "Hello"
        )
        
        # Check if this chatbot has n8n integration enabled
        chatbot_config = chatbot_configs.get(chatbot_id, {})
        
        if chatbot_config.get('n8n_enabled', False) and N8N_INTEGRATION_AVAILABLE:
            # Route through n8n integration
            try:
                n8n_response = answer_user(message)
                return {"response": n8n_response, "source": "n8n_integration"}
            except Exception as e:
                print(f"n8n integration error for chatbot {chatbot_id}: {e}")
        
        # Fallback response
        fallback_response = await _generate_fallback_response(message)
        return {"response": fallback_response, "source": "fallback"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chatbots/{chatbot_id}/config")
async def update_chatbot_config(chatbot_id: str, config: ChatbotConfig):
    """Update chatbot configuration"""
    chatbot_configs[chatbot_id] = config.dict()
    return {"message": f"Configuration updated for chatbot {chatbot_id}"}

@app.get("/api/chatbots/{chatbot_id}/config")
async def get_chatbot_config(chatbot_id: str):
    """Get chatbot configuration"""
    config = chatbot_configs.get(chatbot_id)
    if not config:
        raise HTTPException(status_code=404, detail="Chatbot configuration not found")
    return config

@app.get("/api/n8n/workflows")
async def get_n8n_workflows(active: Optional[bool] = None, limit: int = 100):
    """Get n8n workflows"""
    if not N8N_INTEGRATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="n8n integration not available")
    
    try:
        params = {"limit": min(limit, 250)}
        if active is not None:
            params["active"] = str(active).lower()
        
        workflows = call_n8n_api("GET", "/workflows", params)
        return {
            "workflows": workflows,
            "count": len(workflows) if isinstance(workflows, list) else 0,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/n8n/executions")
async def get_n8n_executions(
    status: Optional[str] = None,
    workflow_id: Optional[str] = None,
    limit: int = 100
):
    """Get n8n executions"""
    if not N8N_INTEGRATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="n8n integration not available")
    
    try:
        params = {"limit": min(limit, 250)}
        if status:
            params["status"] = status
        if workflow_id:
            params["workflowId"] = workflow_id
        
        executions = call_n8n_api("GET", "/executions", params)
        return {
            "executions": executions,
            "count": len(executions) if isinstance(executions, list) else 0,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== N8N CONFIGURATION ENDPOINTS =====

@app.post("/api/config/n8n")
async def configure_n8n(config_data: N8nConfig):
    """Configure n8n API credentials"""
    if not METRICS_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Configuration service not available")
    
    # Validate configuration
    validation = config_service.validate_config(config_data.api_url, config_data.api_key)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail={"errors": validation["errors"]})
    
    # Save configuration
    success = config_service.save_config(
        config_data.api_url,
        config_data.api_key,
        config_data.instance_name
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save configuration")
    
    # Test connection with new config
    config = config_service.load_config()
    if config:
        connection_success = metrics_service.configure(config["api_url"], config["api_key"])
        return {
            "message": "Configuration saved successfully",
            "connection_test": "successful" if connection_success else "failed",
            "instance_name": config_data.instance_name
        }
    
    return {"message": "Configuration saved but connection test failed"}

@app.get("/api/config/n8n/status")
async def get_config_status():
    """Get n8n configuration status"""
    if not METRICS_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Configuration service not available")
    
    status = config_service.get_config_status()
    
    # Test connection if configured
    if status["configured"]:
        connection_healthy = False
        try:
            config = config_service.load_config()
            if config:
                connection_healthy = metrics_service.configure(config["api_url"], config["api_key"])
        except:
            pass
        
        status["connection_healthy"] = connection_healthy
        status["masked_api_key"] = config_service.get_masked_api_key()
    
    return status

@app.delete("/api/config/n8n")
async def delete_n8n_config():
    """Delete n8n configuration"""
    if not METRICS_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Configuration service not available")
    
    success = config_service.delete_config()
    if success:
        return {"message": "Configuration deleted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete configuration")

@app.post("/api/config/n8n/test")
async def test_n8n_connection(config_data: N8nConfig):
    """Test n8n connection without saving configuration"""
    if not METRICS_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Configuration service not available")
    
    try:
        # Create temporary metrics service instance
        temp_service = metrics_service.__class__()
        connection_success = temp_service.configure(config_data.api_url, config_data.api_key)
        
        if connection_success:
            # Get basic info to verify connection
            workflows = temp_service.get_workflows_metrics()
            return {
                "connection": "successful",
                "message": "Successfully connected to n8n instance",
                "workflows_found": workflows.get("total_workflows", 0)
            }
        else:
            return {
                "connection": "failed",
                "message": "Could not connect to n8n instance. Please check your URL and API key."
            }
    except Exception as e:
        return {
            "connection": "failed",
            "message": f"Connection test failed: {str(e)}"
        }

# ===== METRICS ENDPOINTS =====

@app.get("/api/metrics/fast")
async def get_fast_metrics():
    """Get essential metrics with fast loading and caching"""
    if not METRICS_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Metrics service not available")
    
    # Check cache first
    cache_key = "fast_metrics"
    cached_metrics = metrics_cache.get(cache_key)
    if cached_metrics:
        return cached_metrics
    
    # Load configuration - try config service first, fall back to hardcoded values
    config = None
    try:
        config = config_service.load_config()
    except:
        pass  # Config service might not be available
    
    if not config:
        # Fall back to hardcoded configuration from config.py
        try:
            from config import N8N_API_URL, N8N_API_KEY
            config = {
                "api_url": N8N_API_URL,
                "api_key": N8N_API_KEY
            }
        except ImportError:
            raise HTTPException(status_code=400, detail="n8n not configured. Please configure your n8n instance first.")
    
    # Configure metrics service
    if not metrics_service.configure(config["api_url"], config["api_key"]):
        raise HTTPException(status_code=500, detail="Failed to connect to n8n instance")
    
    # Get fast metrics with parallel API calls
    metrics = metrics_service.get_fast_metrics()
    
    if metrics["status"] == "error":
        raise HTTPException(status_code=500, detail=metrics["error"])
    
    # Cache the results
    metrics_cache.set(cache_key, metrics)
    
    return metrics

@app.get("/api/metrics/dashboard")
async def get_dashboard_metrics(execution_days: int = 7):
    """Get comprehensive dashboard metrics"""
    if not METRICS_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Metrics service not available")
    
    # Check cache first
    cache_key = f"dashboard_metrics_{execution_days}"
    cached_metrics = metrics_cache.get(cache_key)
    if cached_metrics:
        return cached_metrics
    
    # Load configuration - try config service first, fall back to hardcoded values
    config = None
    try:
        config = config_service.load_config()
    except:
        pass  # Config service might not be available
    
    if not config:
        # Fall back to hardcoded configuration from config.py
        try:
            from config import N8N_API_URL, N8N_API_KEY
            config = {
                "api_url": N8N_API_URL,
                "api_key": N8N_API_KEY
            }
        except ImportError:
            raise HTTPException(status_code=400, detail="n8n not configured. Please configure your n8n instance first.")
    
    # Configure metrics service
    if not metrics_service.configure(config["api_url"], config["api_key"]):
        raise HTTPException(status_code=500, detail="Failed to connect to n8n instance")
    
    # Get comprehensive metrics
    metrics = metrics_service.get_comprehensive_metrics(execution_days)
    
    if metrics["status"] == "error":
        raise HTTPException(status_code=500, detail=metrics["error"])
    
    # Cache the results
    metrics_cache.set(cache_key, metrics)
    
    return metrics

@app.get("/api/metrics/workflows")
async def get_workflow_metrics():
    """Get workflow-specific metrics"""
    if not METRICS_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Metrics service not available")
    
    config = config_service.load_config()
    if not config:
        raise HTTPException(status_code=400, detail="n8n not configured")
    
    if not metrics_service.configure(config["api_url"], config["api_key"]):
        raise HTTPException(status_code=500, detail="Failed to connect to n8n")
    
    return metrics_service.get_workflows_metrics()

@app.get("/api/metrics/executions")
async def get_execution_metrics(days: int = 7):
    """Get execution-specific metrics"""
    if not METRICS_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Metrics service not available")
    
    config = config_service.load_config()
    if not config:
        raise HTTPException(status_code=400, detail="n8n not configured")
    
    if not metrics_service.configure(config["api_url"], config["api_key"]):
        raise HTTPException(status_code=500, detail="Failed to connect to n8n")
    
    return metrics_service.get_executions_metrics(days)

@app.get("/api/metrics/users")
async def get_user_metrics():
    """Get user-specific metrics"""
    if not METRICS_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Metrics service not available")
    
    config = config_service.load_config()
    if not config:
        raise HTTPException(status_code=400, detail="n8n not configured")
    
    if not metrics_service.configure(config["api_url"], config["api_key"]):
        raise HTTPException(status_code=500, detail="Failed to connect to n8n")
    
    return metrics_service.get_users_metrics()

@app.get("/api/metrics/system")
async def get_system_metrics():
    """Get system-specific metrics"""
    if not METRICS_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Metrics service not available")
    
    config = config_service.load_config()
    if not config:
        raise HTTPException(status_code=400, detail="n8n not configured")
    
    if not metrics_service.configure(config["api_url"], config["api_key"]):
        raise HTTPException(status_code=500, detail="Failed to connect to n8n")
    
    return metrics_service.get_system_metrics()

# Helper functions
async def _is_n8n_related_query(message: str) -> bool:
    """Determine if a message is related to n8n functionality"""
    n8n_keywords = [
        'workflow', 'execution', 'node', 'trigger', 'automation',
        'n8n', 'api', 'webhook', 'credential', 'variable', 'project',
        'activate', 'deactivate', 'run', 'execute', 'schedule',
        'user', 'tag', 'audit', 'source control'
    ]
    
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in n8n_keywords)

async def _generate_fallback_response(message: str) -> str:
    """Generate a fallback response when n8n integration is not available or not applicable"""
    responses = [
        f"I understand you're asking about: '{message}'. I'm a FlowMastery assistant, and I can help with workflow automation and chatbot management.",
        f"Thanks for your message: '{message}'. I can assist with n8n workflows, executions, and automation tasks.",
        f"I received your query: '{message}'. For n8n-specific operations, please ensure your n8n integration is properly configured.",
    ]
    
    # Simple response selection (in production, you might want more sophisticated NLP)
    import hashlib
    hash_obj = hashlib.md5(message.encode())
    response_index = int(hash_obj.hexdigest(), 16) % len(responses)
    
    return responses[response_index]

if __name__ == "__main__":
    print("🚀 Starting FlowMastery Backend Server...")
    print(f"📡 n8n Integration Available: {N8N_INTEGRATION_AVAILABLE}")
    
    if N8N_INTEGRATION_AVAILABLE:
        print(f"🔗 n8n API URL: {N8N_API_URL}")
        print(f"🤖 AI Model: {'Gemini' if GEMINI_API_KEY else 'None'}")
    
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
