"""Configuration endpoints"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any

from app.services.config_service import config_service

router = APIRouter()


@router.get("/n8n/status")
async def get_n8n_config_status() -> Dict[str, Any]:
    """Get n8n configuration status"""
    result = await config_service.get_n8n_config_status()
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error
        )
    
    return result.data


@router.get("/ai/status")
async def get_ai_config_status() -> Dict[str, Any]:
    """Get AI services configuration status"""
    result = await config_service.get_ai_config_status()
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error
        )
    
    return result.data


@router.get("/app/status")
async def get_app_config_status() -> Dict[str, Any]:
    """Get application configuration status"""
    result = await config_service.get_app_config_status()
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error
        )
    
    return result.data


@router.get("/status")
async def get_full_config_status() -> Dict[str, Any]:
    """Get comprehensive configuration status"""
    result = await config_service.get_full_config_status()
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error
        )
    
    return result.data