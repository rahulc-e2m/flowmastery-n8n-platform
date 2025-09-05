from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
import logging

from app.core.dependencies import get_db, get_current_user
from app.core.user_roles import UserRole
from app.core.user_roles import RolePermissions
from app.models.user import User
from app.services.guide_service import GuideService
from app.schemas.guide import (
    GuideCreate, 
    GuideUpdate, 
    GuideResponse, 
    GuideListResponse
)
from app.core.decorators import validate_input, sanitize_response
from app.core.response_formatter import format_response

router = APIRouter(tags=["guides"])
logger = logging.getLogger(__name__)


def get_guide_service(db: AsyncSession = Depends(get_db)) -> GuideService:
    """Dependency injection for GuideService"""
    return GuideService(db)


def get_admin_user():
    """Get admin user dependency"""
    return get_current_user(required_roles=[UserRole.ADMIN])


@router.get("/")
@format_response(message="Guides retrieved successfully")
async def get_guides(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by platform name"),
    current_user: User = Depends(get_current_user()),
    guide_service: GuideService = Depends(get_guide_service)
):
    """
    Get paginated list of guides.
    Accessible by all authenticated users.
    """
    return await guide_service.get_guides(
        page=page,
        per_page=per_page,
        search=search
    )


@router.get("/{guide_id}")
@format_response(message="Guide retrieved successfully")
async def get_guide(
    guide_id: UUID,
    current_user: User = Depends(get_current_user()),
    guide_service: GuideService = Depends(get_guide_service)
):
    """
    Get a specific guide by ID.
    Accessible by all authenticated users.
    """
    guide = await guide_service.get_guide_by_id(guide_id)
    if not guide:
        raise HTTPException(status_code=404, detail="Guide not found")
    return guide


@router.post("/")
@validate_input(max_string_length=1000, validate_urls=True, skip_sql_check_fields=['description', 'title', 'platform_name'])
@sanitize_response()
@format_response(message="Guide created successfully", status_code=201)
async def create_guide(
    guide_data: GuideCreate,
    current_user: User = Depends(get_admin_user()),
    guide_service: GuideService = Depends(get_guide_service)
):
    """
    Create a new guide.
    Admin access required.
    """
    return await guide_service.create_guide(guide_data)


@router.put("/{guide_id}")
@validate_input(max_string_length=1000, validate_urls=False, skip_sql_check_fields=['description', 'title', 'platform_name', 'where_to_get', 'guide_link', 'documentation_link'])
@sanitize_response()
@format_response(message="Guide updated successfully")
async def update_guide(
    guide_id: UUID,
    guide_data: GuideUpdate,
    current_user: User = Depends(get_admin_user()),
    guide_service: GuideService = Depends(get_guide_service)
):
    """
    Update an existing guide.
    Admin access required.
    """
    logger.info(f"Update guide endpoint called for ID: {guide_id}")
    logger.info(f"User: {current_user.email}")
    logger.info(f"Guide data received: {guide_data.model_dump()}")
    
    try:
        updated_guide = await guide_service.update_guide(
            guide_id, guide_data
        )
        if not updated_guide:
            logger.warning(f"Guide not found for update: {guide_id}")
            raise HTTPException(status_code=404, detail="Guide not found")
        
        logger.info(f"Guide updated successfully: {updated_guide.platform_name}")
        return updated_guide
    
    except HTTPException as e:
        logger.error(f"HTTP Exception in update_guide: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in update_guide endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{guide_id}")
@format_response(message="Guide deleted successfully")
async def delete_guide(
    guide_id: UUID,
    current_user: User = Depends(get_admin_user()),
    guide_service: GuideService = Depends(get_guide_service)
):
    """
    Delete a guide.
    Admin access required.
    """
    success = await guide_service.delete_guide(guide_id)
    if not success:
        raise HTTPException(status_code=404, detail="Guide not found")
    
    return {"message": "Guide deleted successfully"}


@router.get("/platform/{platform_name}")
@format_response(message="Guide retrieved successfully")
async def get_guide_by_platform(
    platform_name: str,
    current_user: User = Depends(get_current_user()),
    guide_service: GuideService = Depends(get_guide_service)
):
    """
    Get a guide by platform name.
    Accessible by all authenticated users.
    """
    guide = await guide_service.get_guide_by_platform_name(platform_name)
    if not guide:
        raise HTTPException(
            status_code=404, 
            detail=f"Guide for platform '{platform_name}' not found"
        )
    return guide
