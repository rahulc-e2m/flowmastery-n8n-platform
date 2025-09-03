"""Configuration endpoints"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any

from app.services.config_service import config_service
from app.core.response_formatter import format_response
from app.schemas.config import ConfigStatusResponse, N8nConfigStatus, AiConfigStatus, AppConfigStatus, FullConfigStatus

router = APIRouter()


@router.get("/n8n/status")
@format_response(message="n8n configuration status retrieved successfully")
async def get_n8n_config_status():
    """Get n8n configuration status"""
    result = await config_service.get_n8n_config_status()
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error
        )
    
    # Convert result.data to N8nConfigStatus
    n8n_status = N8nConfigStatus(
        configured=result.data.get("configured", False),
        api_url=result.data.get("api_url"),
        last_tested=result.data.get("last_tested"),
        status=result.data.get("status"),
        error=result.data.get("error")
    )
    
    return ConfigStatusResponse(
        status="success",
        details=FullConfigStatus(
            n8n=n8n_status,
            ai=AiConfigStatus(
                openai_configured=False,
                anthropic_configured=False,
                openai_model=None,
                anthropic_model=None
            ),
            app=AppConfigStatus(
                environment="unknown",
                debug_mode=False,
                cors_enabled=False,
                rate_limiting_enabled=False
            )
        )
    )


@router.get("/ai/status")
@format_response(message="AI services configuration status retrieved successfully")
async def get_ai_config_status():
    """Get AI services configuration status"""
    result = await config_service.get_ai_config_status()
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error
        )
    
    # Convert result.data to AiConfigStatus
    ai_status = AiConfigStatus(
        openai_configured=result.data.get("openai_configured", False),
        anthropic_configured=result.data.get("anthropic_configured", False),
        openai_model=result.data.get("openai_model"),
        anthropic_model=result.data.get("anthropic_model")
    )
    
    return ConfigStatusResponse(
        status="success",
        details=FullConfigStatus(
            n8n=N8nConfigStatus(
                configured=False,
                api_url=None,
                last_tested=None,
                status=None,
                error=None
            ),
            ai=ai_status,
            app=AppConfigStatus(
                environment="unknown",
                debug_mode=False,
                cors_enabled=False,
                rate_limiting_enabled=False
            )
        )
    )


@router.get("/app/status")
@format_response(message="Application configuration status retrieved successfully")
async def get_app_config_status():
    """Get application configuration status"""
    result = await config_service.get_app_config_status()
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error
        )
    
    # Convert result.data to AppConfigStatus
    app_status = AppConfigStatus(
        environment=result.data.get("environment", "unknown"),
        debug_mode=result.data.get("debug_mode", False),
        cors_enabled=result.data.get("cors_enabled", False),
        rate_limiting_enabled=result.data.get("rate_limiting_enabled", False)
    )
    
    return ConfigStatusResponse(
        status="success",
        details=FullConfigStatus(
            n8n=N8nConfigStatus(
                configured=False,
                api_url=None,
                last_tested=None,
                status=None,
                error=None
            ),
            ai=AiConfigStatus(
                openai_configured=False,
                anthropic_configured=False,
                openai_model=None,
                anthropic_model=None
            ),
            app=app_status
        )
    )


@router.get("/status")
@format_response(message="Comprehensive configuration status retrieved successfully")
async def get_full_config_status():
    """Get comprehensive configuration status"""
    result = await config_service.get_full_config_status()
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error
        )
    
    # Convert result.data to FullConfigStatus
    full_status = FullConfigStatus(
        n8n=N8nConfigStatus(
            configured=result.data.get("n8n", {}).get("configured", False),
            api_url=result.data.get("n8n", {}).get("api_url"),
            last_tested=result.data.get("n8n", {}).get("last_tested"),
            status=result.data.get("n8n", {}).get("status"),
            error=result.data.get("n8n", {}).get("error")
        ),
        ai=AiConfigStatus(
            openai_configured=result.data.get("ai", {}).get("openai_configured", False),
            anthropic_configured=result.data.get("ai", {}).get("anthropic_configured", False),
            openai_model=result.data.get("ai", {}).get("openai_model"),
            anthropic_model=result.data.get("ai", {}).get("anthropic_model")
        ),
        app=AppConfigStatus(
            environment=result.data.get("app", {}).get("environment", "unknown"),
            debug_mode=result.data.get("app", {}).get("debug_mode", False),
            cors_enabled=result.data.get("app", {}).get("cors_enabled", False),
            rate_limiting_enabled=result.data.get("app", {}).get("rate_limiting_enabled", False)
        )
    )
    
    return ConfigStatusResponse(
        status="success",
        details=full_status
    )