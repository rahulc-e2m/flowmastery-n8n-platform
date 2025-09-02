"""
Base Entity Service - Provides CRUD operations through the service layer

This service provides standardized CRUD operations for database entities
with built-in caching, rate limiting, and database protection.
"""

from typing import Any, Dict, List, Optional, Type, TypeVar, Generic, Union
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import DeclarativeBase
from pydantic import BaseModel

from app.core.service_layer import (
    BaseService, OperationContext, OperationType, OperationResult,
    ValidationError, DatabaseOverloadError
)

T = TypeVar('T', bound=DeclarativeBase)
CreateSchema = TypeVar('CreateSchema', bound=BaseModel)
UpdateSchema = TypeVar('UpdateSchema', bound=BaseModel)


class BaseEntityService(BaseService[T], Generic[T, CreateSchema, UpdateSchema]):
    """Base service for entity CRUD operations"""
    
    def __init__(self, model_class: Type[T], **kwargs):
        super().__init__(**kwargs)
        self.model_class = model_class
        self._service_name = f"{model_class.__name__.lower()}_service"
    
    @property
    def service_name(self) -> str:
        return self._service_name
    
    def _get_cache_key(self, operation: str, *args) -> str:
        """Generate cache key for entity operations"""
        return f"{self.service_name}:{operation}:{':'.join(str(arg) for arg in args)}"
    
    async def _validate_create_input(self, data: CreateSchema, context: OperationContext) -> None:
        """Validate create input data"""
        if not data:
            raise ValidationError("Create data cannot be empty")
        
        # Additional validation can be implemented in subclasses
        await self._validate_input(data, context)
    
    async def _validate_update_input(self, data: UpdateSchema, context: OperationContext) -> None:
        """Validate update input data"""
        if not data:
            raise ValidationError("Update data cannot be empty")
        
        # Additional validation can be implemented in subclasses
        await self._validate_input(data, context)
    
    async def create(
        self,
        data: CreateSchema,
        context: OperationContext,
        commit: bool = True
    ) -> OperationResult[T]:
        """Create a new entity"""
        context.operation_type = OperationType.CREATE
        
        async def _create_operation():
            await self._validate_create_input(data, context)
            
            async with self._get_db_session() as db:
                # Convert Pydantic model to dict, excluding unset fields
                create_data = data.model_dump(exclude_unset=True)
                
                # Create entity instance
                entity = self.model_class(**create_data)
                
                # Add to session
                db.add(entity)
                
                if commit:
                    await db.commit()
                    await db.refresh(entity)
                
                # Invalidate relevant cache entries
                await self._invalidate_cache(f"{self.service_name}:list:*")
                await self._invalidate_cache(f"{self.service_name}:count:*")
                
                return entity
        
        return await self.execute_operation(_create_operation, context)
    
    async def get_by_id(
        self,
        entity_id: Union[str, int],
        context: OperationContext,
        use_cache: bool = True
    ) -> OperationResult[Optional[T]]:
        """Get entity by ID"""
        context.operation_type = OperationType.READ
        
        async def _get_operation():
            cache_key = self._get_cache_key("get", entity_id)
            
            # Try cache first
            if use_cache:
                cached_result = await self._get_from_cache(cache_key)
                if cached_result is not None:
                    return cached_result
            
            async with self._get_db_session() as db:
                stmt = select(self.model_class).where(self.model_class.id == entity_id)
                result = await db.execute(stmt)
                entity = result.scalar_one_or_none()
                
                # Cache the result
                if use_cache and entity:
                    await self._set_cache(cache_key, entity)
                
                return entity
        
        return await self.execute_operation(_get_operation, context)
    
    async def list_entities(
        self,
        context: OperationContext,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None,
        use_cache: bool = True
    ) -> OperationResult[List[T]]:
        """List entities with optional filtering and pagination"""
        context.operation_type = OperationType.READ
        
        # Enforce maximum batch size
        if limit and limit > self.config.max_batch_size:
            limit = self.config.max_batch_size
        
        async def _list_operation():
            # Generate cache key based on parameters
            cache_params = [
                str(filters or {}),
                str(limit or ""),
                str(offset or ""),
                str(order_by or "")
            ]
            cache_key = self._get_cache_key("list", *cache_params)
            
            # Try cache first
            if use_cache:
                cached_result = await self._get_from_cache(cache_key)
                if cached_result is not None:
                    return cached_result
            
            async with self._get_db_session() as db:
                stmt = select(self.model_class)
                
                # Apply filters
                if filters:
                    for field, value in filters.items():
                        if hasattr(self.model_class, field):
                            stmt = stmt.where(getattr(self.model_class, field) == value)
                
                # Apply ordering
                if order_by and hasattr(self.model_class, order_by):
                    stmt = stmt.order_by(getattr(self.model_class, order_by))
                
                # Apply pagination
                if offset:
                    stmt = stmt.offset(offset)
                if limit:
                    stmt = stmt.limit(limit)
                
                result = await db.execute(stmt)
                entities = result.scalars().all()
                
                # Cache the result
                if use_cache:
                    await self._set_cache(cache_key, entities)
                
                return list(entities)
        
        return await self.execute_operation(_list_operation, context)
    
    async def update(
        self,
        entity_id: Union[str, int],
        data: UpdateSchema,
        context: OperationContext,
        commit: bool = True
    ) -> OperationResult[Optional[T]]:
        """Update an entity"""
        context.operation_type = OperationType.UPDATE
        
        async def _update_operation():
            await self._validate_update_input(data, context)
            
            async with self._get_db_session() as db:
                # Get existing entity
                stmt = select(self.model_class).where(self.model_class.id == entity_id)
                result = await db.execute(stmt)
                entity = result.scalar_one_or_none()
                
                if not entity:
                    return None
                
                # Update fields
                update_data = data.model_dump(exclude_unset=True)
                for field, value in update_data.items():
                    if hasattr(entity, field):
                        setattr(entity, field, value)
                
                if commit:
                    await db.commit()
                    await db.refresh(entity)
                
                # Invalidate cache
                await self._invalidate_cache(f"{self.service_name}:get:{entity_id}")
                await self._invalidate_cache(f"{self.service_name}:list:*")
                
                return entity
        
        return await self.execute_operation(_update_operation, context)
    
    async def delete(
        self,
        entity_id: Union[str, int],
        context: OperationContext,
        commit: bool = True
    ) -> OperationResult[bool]:
        """Delete an entity"""
        context.operation_type = OperationType.DELETE
        
        async def _delete_operation():
            async with self._get_db_session() as db:
                stmt = delete(self.model_class).where(self.model_class.id == entity_id)
                result = await db.execute(stmt)
                
                if commit:
                    await db.commit()
                
                # Invalidate cache
                await self._invalidate_cache(f"{self.service_name}:get:{entity_id}")
                await self._invalidate_cache(f"{self.service_name}:list:*")
                await self._invalidate_cache(f"{self.service_name}:count:*")
                
                return result.rowcount > 0
        
        return await self.execute_operation(_delete_operation, context)
    
    async def count(
        self,
        context: OperationContext,
        filters: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> OperationResult[int]:
        """Count entities with optional filtering"""
        context.operation_type = OperationType.READ
        
        async def _count_operation():
            cache_key = self._get_cache_key("count", str(filters or {}))
            
            # Try cache first
            if use_cache:
                cached_result = await self._get_from_cache(cache_key)
                if cached_result is not None:
                    return cached_result
            
            async with self._get_db_session() as db:
                stmt = select(func.count(self.model_class.id))
                
                # Apply filters
                if filters:
                    for field, value in filters.items():
                        if hasattr(self.model_class, field):
                            stmt = stmt.where(getattr(self.model_class, field) == value)
                
                result = await db.execute(stmt)
                count = result.scalar()
                
                # Cache the result
                if use_cache:
                    await self._set_cache(cache_key, count)
                
                return count
        
        return await self.execute_operation(_count_operation, context)
    
    async def bulk_create(
        self,
        data_list: List[CreateSchema],
        context: OperationContext,
        commit: bool = True
    ) -> OperationResult[List[T]]:
        """Bulk create entities"""
        context.operation_type = OperationType.BULK_CREATE
        
        # Enforce batch size limit
        if len(data_list) > self.config.max_batch_size:
            raise ValidationError(f"Batch size {len(data_list)} exceeds maximum {self.config.max_batch_size}")
        
        async def _bulk_create_operation():
            entities = []
            
            async with self._get_db_session() as db:
                for data in data_list:
                    await self._validate_create_input(data, context)
                    create_data = data.model_dump(exclude_unset=True)
                    entity = self.model_class(**create_data)
                    entities.append(entity)
                    db.add(entity)
                
                if commit:
                    await db.commit()
                    for entity in entities:
                        await db.refresh(entity)
                
                # Invalidate cache
                await self._invalidate_cache(f"{self.service_name}:list:*")
                await self._invalidate_cache(f"{self.service_name}:count:*")
                
                return entities
        
        return await self.execute_operation(_bulk_create_operation, context)
    
    async def exists(
        self,
        entity_id: Union[str, int],
        context: OperationContext,
        use_cache: bool = True
    ) -> OperationResult[bool]:
        """Check if entity exists"""
        context.operation_type = OperationType.READ
        
        async def _exists_operation():
            cache_key = self._get_cache_key("exists", entity_id)
            
            # Try cache first
            if use_cache:
                cached_result = await self._get_from_cache(cache_key)
                if cached_result is not None:
                    return cached_result
            
            async with self._get_db_session() as db:
                stmt = select(func.count(self.model_class.id)).where(self.model_class.id == entity_id)
                result = await db.execute(stmt)
                exists = result.scalar() > 0
                
                # Cache the result
                if use_cache:
                    await self._set_cache(cache_key, exists)
                
                return exists
        
        return await self.execute_operation(_exists_operation, context)