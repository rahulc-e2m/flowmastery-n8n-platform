from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from sqlalchemy.exc import IntegrityError
from uuid import UUID
from datetime import datetime, timezone

from app.models.dependency import Dependency
from app.schemas.dependency import DependencyCreate, DependencyUpdate, DependencyResponse, DependencyListResponse
from app.core.exceptions import HTTPException


class DependencyService:
    """Service for managing platform dependencies and guides"""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dependencies(
        self, 
        page: int = 1, 
        per_page: int = 50, 
        search: Optional[str] = None
    ) -> DependencyListResponse:
        """Get paginated list of dependencies with optional search"""
        offset = (page - 1) * per_page
        
        # Build query
        query = select(Dependency)
        count_query = select(func.count(Dependency.id))
        
        if search:
            search_filter = Dependency.platform_name.ilike(f"%{search}%")
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        # Order by platform name
        query = query.order_by(Dependency.platform_name).offset(offset).limit(per_page)
        
        # Execute queries
        result = await self.db.execute(query)
        dependencies = result.scalars().all()
        
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        # Convert to response models
        dependency_responses = [
            DependencyResponse.model_validate(dep) for dep in dependencies
        ]
        
        return DependencyListResponse(
            dependencies=dependency_responses,
            total=total,
            page=page,
            per_page=per_page
        )

    async def get_dependency_by_id(self, dependency_id: UUID) -> Optional[DependencyResponse]:
        """Get a specific dependency by ID"""
        query = select(Dependency).where(Dependency.id == dependency_id)
        result = await self.db.execute(query)
        dependency = result.scalar_one_or_none()
        
        if dependency:
            return DependencyResponse.model_validate(dependency)
        return None

    async def get_dependency_by_platform_name(self, platform_name: str) -> Optional[DependencyResponse]:
        """Get a specific dependency by platform name"""
        query = select(Dependency).where(Dependency.platform_name == platform_name)
        result = await self.db.execute(query)
        dependency = result.scalar_one_or_none()
        
        if dependency:
            return DependencyResponse.model_validate(dependency)
        return None

    async def create_dependency(self, dependency_data: DependencyCreate) -> DependencyResponse:
        """Create a new dependency"""
        try:
            # Check if platform name already exists
            existing = await self.get_dependency_by_platform_name(dependency_data.platform_name)
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Dependency with platform name '{dependency_data.platform_name}' already exists"
                )
            
            dependency = Dependency(**dependency_data.model_dump())
            self.db.add(dependency)
            await self.db.commit()
            await self.db.refresh(dependency)
            
            return DependencyResponse.model_validate(dependency)
            
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=400,
                detail="Dependency with this platform name already exists"
            )

    async def update_dependency(
        self, 
        dependency_id: UUID, 
        dependency_data: DependencyUpdate
    ) -> Optional[DependencyResponse]:
        """Update an existing dependency"""
        try:
            # Get current dependency
            existing = await self.get_dependency_by_id(dependency_id)
            if not existing:
                return None
            
            # Check for platform name conflicts if platform_name is being updated
            if dependency_data.platform_name and dependency_data.platform_name != existing.platform_name:
                conflict = await self.get_dependency_by_platform_name(dependency_data.platform_name)
                if conflict and conflict.id != dependency_id:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Dependency with platform name '{dependency_data.platform_name}' already exists"
                    )
            
            # Prepare update data
            update_data = {
                k: v for k, v in dependency_data.model_dump().items() 
                if v is not None
            }
            update_data["updated_at"] = datetime.now(timezone.utc)
            
            # Update dependency
            stmt = (
                update(Dependency)
                .where(Dependency.id == dependency_id)
                .values(**update_data)
                .returning(Dependency)
            )
            
            result = await self.db.execute(stmt)
            updated_dependency = result.scalar_one()
            await self.db.commit()
            
            return DependencyResponse.model_validate(updated_dependency)
            
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=400,
                detail="Dependency with this platform name already exists"
            )

    async def delete_dependency(self, dependency_id: UUID) -> bool:
        """Delete a dependency"""
        # Check if dependency exists
        existing = await self.get_dependency_by_id(dependency_id)
        if not existing:
            return False
        
        # Delete dependency
        stmt = delete(Dependency).where(Dependency.id == dependency_id)
        await self.db.execute(stmt)
        await self.db.commit()
        
        return True

    async def bulk_create_dependencies(self, dependencies_data: List[DependencyCreate]) -> List[DependencyResponse]:
        """Bulk create dependencies"""
        created_dependencies = []
        
        for dependency_data in dependencies_data:
            try:
                dependency = Dependency(**dependency_data.model_dump())
                self.db.add(dependency)
                created_dependencies.append(dependency)
            except Exception as e:
                # Skip duplicates and continue
                continue
        
        if created_dependencies:
            await self.db.commit()
            for dep in created_dependencies:
                await self.db.refresh(dep)
        
        return [DependencyResponse.model_validate(dep) for dep in created_dependencies]