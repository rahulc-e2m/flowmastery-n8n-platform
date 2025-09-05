from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from sqlalchemy.exc import IntegrityError
from uuid import UUID
from datetime import datetime, timezone
import logging

from app.models.guide import Guide
from app.schemas.guide import GuideCreate, GuideUpdate, GuideResponse, GuideListResponse
from app.core.exceptions import HTTPException

logger = logging.getLogger(__name__)


class GuideService:
    """Service for managing platform guides and instructions"""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_guides(
        self, 
        page: int = 1, 
        per_page: int = 50, 
        search: Optional[str] = None
    ) -> GuideListResponse:
        """Get paginated list of guides with optional search"""
        offset = (page - 1) * per_page
        
        # Build query
        query = select(Guide)
        count_query = select(func.count(Guide.id))
        
        if search:
            search_filter = Guide.platform_name.ilike(f"%{search}%")
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        # Order by platform name
        query = query.order_by(Guide.platform_name).offset(offset).limit(per_page)
        
        # Execute queries
        result = await self.db.execute(query)
        guides = result.scalars().all()
        
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        # Convert to response models
        guide_responses = [
            GuideResponse.model_validate(guide) for guide in guides
        ]
        
        return GuideListResponse(
            guides=guide_responses,
            total=total,
            page=page,
            per_page=per_page
        )

    async def get_guide_by_id(self, guide_id: UUID) -> Optional[GuideResponse]:
        """Get a specific guide by ID"""
        query = select(Guide).where(Guide.id == guide_id)
        result = await self.db.execute(query)
        guide = result.scalar_one_or_none()
        
        if guide:
            return GuideResponse.model_validate(guide)
        return None

    async def get_guide_by_platform_name(self, platform_name: str) -> Optional[GuideResponse]:
        """Get a specific guide by platform name"""
        query = select(Guide).where(Guide.platform_name == platform_name)
        result = await self.db.execute(query)
        guide = result.scalar_one_or_none()
        
        if guide:
            return GuideResponse.model_validate(guide)
        return None

    async def create_guide(self, guide_data: GuideCreate) -> GuideResponse:
        """Create a new guide"""
        try:
            # Check if platform name already exists
            existing = await self.get_guide_by_platform_name(guide_data.platform_name)
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Guide with platform name '{guide_data.platform_name}' already exists"
                )
            
            guide = Guide(**guide_data.model_dump())
            self.db.add(guide)
            await self.db.commit()
            await self.db.refresh(guide)
            
            return GuideResponse.model_validate(guide)
            
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=400,
                detail="Guide with this platform name already exists"
            )

    async def update_guide(
        self, 
        guide_id: UUID, 
        guide_data: GuideUpdate
    ) -> Optional[GuideResponse]:
        """Update an existing guide"""
        logger.info(f"Starting guide update for ID: {guide_id}")
        logger.info(f"Update data: {guide_data.model_dump()}")
        
        try:
            # Get current guide
            logger.info("Fetching existing guide...")
            existing = await self.get_guide_by_id(guide_id)
            if not existing:
                logger.warning(f"Guide not found for ID: {guide_id}")
                return None
            
            logger.info(f"Found existing guide: {existing.platform_name}")
            
            # Check for platform name conflicts if platform_name is being updated
            if guide_data.platform_name and guide_data.platform_name != existing.platform_name:
                logger.info(f"Checking platform name conflicts for: {guide_data.platform_name}")
                conflict = await self.get_guide_by_platform_name(guide_data.platform_name)
                if conflict and conflict.id != guide_id:
                    logger.error(f"Platform name conflict detected: {guide_data.platform_name}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Guide with platform name '{guide_data.platform_name}' already exists"
                    )
            
            # Prepare update data
            logger.info("Preparing update data...")
            update_data = {
                k: v for k, v in guide_data.model_dump().items() 
                if v is not None
            }
            update_data["updated_at"] = datetime.now()  # Use naive datetime to match DB schema
            logger.info(f"Final update data: {update_data}")
            
            # Update guide
            logger.info("Executing database update...")
            stmt = (
                update(Guide)
                .where(Guide.id == guide_id)
                .values(**update_data)
                .returning(Guide)
            )
            
            logger.info(f"SQL Statement prepared for guide ID: {guide_id}")
            result = await self.db.execute(stmt)
            logger.info("SQL executed, getting result...")
            updated_guide = result.scalar_one()
            logger.info("Committing transaction...")
            await self.db.commit()
            logger.info("Guide update completed successfully")
            
            return GuideResponse.model_validate(updated_guide)
            
        except IntegrityError as e:
            logger.error(f"IntegrityError during guide update: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=400,
                detail="Guide with this platform name already exists"
            )
        except Exception as e:
            logger.error(f"Unexpected error during guide update: {str(e)}", exc_info=True)
            await self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update guide: {str(e)}"
            )

    async def delete_guide(self, guide_id: UUID) -> bool:
        """Delete a guide"""
        # Check if guide exists
        existing = await self.get_guide_by_id(guide_id)
        if not existing:
            return False
        
        # Delete guide
        stmt = delete(Guide).where(Guide.id == guide_id)
        await self.db.execute(stmt)
        await self.db.commit()
        
        return True

    async def bulk_create_guides(self, guides_data: List[GuideCreate]) -> List[GuideResponse]:
        """Bulk create guides"""
        created_guides = []
        
        for guide_data in guides_data:
            try:
                guide = Guide(**guide_data.model_dump())
                self.db.add(guide)
                created_guides.append(guide)
            except Exception as e:
                # Skip duplicates and continue
                continue
        
        if created_guides:
            await self.db.commit()
            for guide in created_guides:
                await self.db.refresh(guide)
        
        return [GuideResponse.model_validate(guide) for guide in created_guides]
