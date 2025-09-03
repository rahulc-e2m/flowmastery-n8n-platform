from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.dependency_service import DependencyService
from app.schemas.dependency import (
    DependencyCreate, 
    DependencyUpdate, 
    DependencyResponse, 
    DependencyListResponse
)
from app.core.decorators import validate_input, sanitize_response
from app.core.response_formatter import format_response

router = APIRouter(prefix="/dependencies", tags=["dependencies"])


def get_dependency_service(db: AsyncSession = Depends(get_db)) -> DependencyService:
    """Dependency injection for DependencyService"""
    return DependencyService(db)


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role for certain operations"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return current_user


@router.get("/")
@format_response(message="Dependencies retrieved successfully")
async def get_dependencies(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by platform name"),
    current_user: User = Depends(get_current_user),
    dependency_service: DependencyService = Depends(get_dependency_service)
):
    """
    Get paginated list of dependencies.
    Accessible by all authenticated users.
    """
    return await dependency_service.get_dependencies(
        page=page,
        per_page=per_page,
        search=search
    )


@router.get("/{dependency_id}")
@format_response(message="Dependency retrieved successfully")
async def get_dependency(
    dependency_id: UUID,
    current_user: User = Depends(get_current_user),
    dependency_service: DependencyService = Depends(get_dependency_service)
):
    """
    Get a specific dependency by ID.
    Accessible by all authenticated users.
    """
    dependency = await dependency_service.get_dependency_by_id(dependency_id)
    if not dependency:
        raise HTTPException(status_code=404, detail="Dependency not found")
    return dependency


@router.post("/")
@validate_input(max_string_length=1000, validate_urls=True)
@sanitize_response()
@format_response(message="Dependency created successfully", status_code=201)
async def create_dependency(
    dependency_data: DependencyCreate,
    current_user: User = Depends(require_admin),
    dependency_service: DependencyService = Depends(get_dependency_service)
):
    """
    Create a new dependency.
    Admin access required.
    """
    return await dependency_service.create_dependency(dependency_data)


@router.put("/{dependency_id}")
@validate_input(max_string_length=1000, validate_urls=True)
@sanitize_response()
@format_response(message="Dependency updated successfully")
async def update_dependency(
    dependency_id: UUID,
    dependency_data: DependencyUpdate,
    current_user: User = Depends(require_admin),
    dependency_service: DependencyService = Depends(get_dependency_service)
):
    """
    Update an existing dependency.
    Admin access required.
    """
    updated_dependency = await dependency_service.update_dependency(
        dependency_id, dependency_data
    )
    if not updated_dependency:
        raise HTTPException(status_code=404, detail="Dependency not found")
    return updated_dependency


@router.delete("/{dependency_id}")
@format_response(message="Dependency deleted successfully")
async def delete_dependency(
    dependency_id: UUID,
    current_user: User = Depends(require_admin),
    dependency_service: DependencyService = Depends(get_dependency_service)
):
    """
    Delete a dependency.
    Admin access required.
    """
    success = await dependency_service.delete_dependency(dependency_id)
    if not success:
        raise HTTPException(status_code=404, detail="Dependency not found")
    
    return {"message": "Dependency deleted successfully"}


@router.get("/platform/{platform_name}")
@format_response(message="Dependency retrieved successfully")
async def get_dependency_by_platform(
    platform_name: str,
    current_user: User = Depends(get_current_user),
    dependency_service: DependencyService = Depends(get_dependency_service)
):
    """
    Get a dependency by platform name.
    Accessible by all authenticated users.
    """
    dependency = await dependency_service.get_dependency_by_platform_name(platform_name)
    if not dependency:
        raise HTTPException(
            status_code=404, 
            detail=f"Dependency for platform '{platform_name}' not found"
        )
    return dependency