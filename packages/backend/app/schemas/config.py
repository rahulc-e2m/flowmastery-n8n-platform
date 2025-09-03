"""Configuration response schemas"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class N8nConfigStatus(BaseModel):
    """n8n configuration status details"""
    configured: bool = Field(description="Whether n8n is configured")
    api_url: Optional[str] = Field(default=None, description="Configured n8n API URL")
    last_tested: Optional[datetime] = Field(default=None, description="When the configuration was last tested")
    status: Optional[str] = Field(default=None, description="Current status (connected, disconnected, etc.)")
    error: Optional[str] = Field(default=None, description="Error message if connection failed")


class AiConfigStatus(BaseModel):
    """AI services configuration status"""
    openai_configured: bool = Field(description="Whether OpenAI is configured")
    anthropic_configured: bool = Field(description="Whether Anthropic is configured")
    openai_model: Optional[str] = Field(default=None, description="Configured OpenAI model")
    anthropic_model: Optional[str] = Field(default=None, description="Configured Anthropic model")


class AppConfigStatus(BaseModel):
    """Application configuration status"""
    environment: str = Field(description="Current environment (development, production, etc.)")
    debug_mode: bool = Field(description="Whether debug mode is enabled")
    cors_enabled: bool = Field(description="Whether CORS is enabled")
    rate_limiting_enabled: bool = Field(description="Whether rate limiting is enabled")


class FullConfigStatus(BaseModel):
    """Complete configuration status"""
    n8n: N8nConfigStatus = Field(description="n8n configuration status")
    ai: AiConfigStatus = Field(description="AI services configuration status")
    app: AppConfigStatus = Field(description="Application configuration status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConfigStatusResponse(BaseModel):
    """Standard response for configuration status"""
    status: str = Field(description="Overall configuration status")
    details: FullConfigStatus = Field(description="Detailed configuration information")
    message: Optional[str] = Field(default=None, description="Additional message")