"""Vistara categories endpoints"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.vistara_category import VistaraCategory
from app.core.dependencies import get_current_user
from app.core.user_roles import RolePermissions
from app.core.role_based_filter import RoleBasedDataFilter
from app.core.decorators import validate_input, sanitize_response
from app.core.response_formatter import format_response

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
@format_response(message="Vistara categories retrieved successfully")
async def get_vistara_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleBasedDataFilter.get_admin_or_client_user())
):
    """Get all vistara categories (global for admin users)"""
    try:
        # Ensure user is admin (Vistara is admin-only)
        if current_user.role != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vistara access is restricted to administrators only"
            )
        
        # Get global Vistara categories (client_id is None for global categories)
        result = await db.execute(
            select(VistaraCategory)
            .filter(VistaraCategory.client_id.is_(None))
            .filter(VistaraCategory.is_active == True)
            .order_by(VistaraCategory.display_order, VistaraCategory.name)
        )
        categories = result.scalars().all()
        
        return [
            {
                "id": str(category.id),
                "name": category.name,
                "description": category.description,
                "color": category.color,
                "icon_name": category.icon_name,
                "display_order": category.display_order,
                "is_system": category.is_system,
                "created_at": category.created_at.isoformat() if category.created_at else None
            }
            for category in categories
        ]
        
    except Exception as e:
        logger.error(f"Error retrieving vistara categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve vistara categories"
        )


@router.post("/")
@validate_input(max_string_length=100)
@sanitize_response()
@format_response(message="Vistara category created successfully")
async def create_vistara_category(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleBasedDataFilter.get_admin_or_client_user())
):
    """Create a new vistara category (global admin category)"""
    try:
        # Ensure user is admin (Vistara is admin-only)
        if current_user.role != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vistara access is restricted to administrators only"
            )
        
        # Validate required fields
        required_fields = ["name", "color"]
        for field in required_fields:
            if field not in payload:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # Get the next display order for global categories
        result = await db.execute(
            select(VistaraCategory.display_order)
            .filter(VistaraCategory.client_id.is_(None))
            .order_by(VistaraCategory.display_order.desc())
            .limit(1)
        )
        max_order = result.scalar()
        next_order = (max_order or 0) + 1
        
        # Create global category (client_id = None)
        category = VistaraCategory(
            client_id=None,  # Global category for admin use
            name=payload["name"],
            description=payload.get("description"),
            color=payload["color"],
            icon_name=payload.get("icon_name"),
            is_active=True,
            display_order=payload.get("display_order", next_order),
            is_system=False,  # User-created categories are never system categories
            created_by=current_user.id
        )
        
        db.add(category)
        await db.commit()
        await db.refresh(category)
        
        return {
            "id": str(category.id),
            "name": category.name,
            "description": category.description,
            "color": category.color,
            "icon_name": category.icon_name,
            "display_order": category.display_order,
            "is_system": category.is_system,
            "created_at": category.created_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating vistara category: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create vistara category"
        )


@router.put("/{category_id}")
@validate_input(max_string_length=100)
@sanitize_response()
@format_response(message="Vistara category updated successfully")
async def update_vistara_category(
    category_id: str,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleBasedDataFilter.get_admin_or_client_user())
):
    """Update a vistara category (global admin category)"""
    try:
        # Ensure user is admin (Vistara is admin-only)
        if current_user.role != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vistara access is restricted to administrators only"
            )
        
        # Get the global category
        result = await db.execute(
            select(VistaraCategory)
            .filter(VistaraCategory.id == category_id)
            .filter(VistaraCategory.client_id.is_(None))
        )
        category = result.scalar_one_or_none()
        
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        # Check if it's a system category
        if category.is_system and not RolePermissions.is_admin(current_user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot modify system categories"
            )
        
        # Update fields
        updatable_fields = ["name", "description", "color", "icon_name", "display_order"]
        for field in updatable_fields:
            if field in payload:
                setattr(category, field, payload[field])
        
        await db.commit()
        await db.refresh(category)
        
        return {
            "id": str(category.id),
            "name": category.name,
            "description": category.description,
            "color": category.color,
            "icon_name": category.icon_name,
            "display_order": category.display_order,
            "is_system": category.is_system,
            "updated_at": category.updated_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating vistara category {category_id}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update vistara category"
        )


@router.delete("/{category_id}")
@format_response(message="Vistara category deleted successfully")
async def delete_vistara_category(
    category_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleBasedDataFilter.get_admin_or_client_user())
):
    """Delete a vistara category (global admin category)"""
    try:
        # Ensure user is admin (Vistara is admin-only)
        if current_user.role != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vistara access is restricted to administrators only"
            )
        
        # Get the global category
        result = await db.execute(
            select(VistaraCategory)
            .filter(VistaraCategory.id == category_id)
            .filter(VistaraCategory.client_id.is_(None))
        )
        category = result.scalar_one_or_none()
        
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        # Check if it's a system category
        if category.is_system:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete system categories"
            )
        
        # Instead of deleting, mark as inactive
        category.is_active = False
        await db.commit()
        
        return {"id": str(category.id)}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting vistara category {category_id}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete vistara category"
        )
