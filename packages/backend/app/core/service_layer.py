"""
Service Layer Core - Mediates between API and Database Operations

This module provides the core service layer architecture that:
1. Acts as a mediator between API calls and database operations
2. Enforces business logic and validation consistently
3. Prevents direct database overload through caching, queuing, and rate limiting
4. Improves maintainability by decoupling API routes from raw database writes
5. Allows easier scaling, monitoring, and debugging
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic, Callable, Union
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from pydantic import BaseModel

from app.services.cache.redis import redis_client
from app.database import get_db

logger = logging.getLogger(__name__)

T = TypeVar('T')
R = TypeVar('R')


class OperationType(Enum):
    """Types of database operations"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    BULK_CREATE = "bulk_create"
    BULK_UPDATE = "bulk_update"
    BULK_DELETE = "bulk_delete"


class CacheStrategy(Enum):
    """Cache strategies for different operations"""
    NO_CACHE = "no_cache"
    READ_THROUGH = "read_through"
    WRITE_THROUGH = "write_through"
    WRITE_BEHIND = "write_behind"
    CACHE_ASIDE = "cache_aside"


@dataclass
class ServiceConfig:
    """Configuration for service layer behavior"""
    # Rate limiting
    max_requests_per_minute: int = 100
    max_concurrent_operations: int = 10
    
    # Caching
    default_cache_ttl: int = 300  # 5 minutes
    cache_strategy: CacheStrategy = CacheStrategy.READ_THROUGH
    
    # Database protection
    max_batch_size: int = 100
    query_timeout: int = 30
    connection_pool_timeout: int = 10
    
    # Retry and circuit breaker
    max_retries: int = 3
    retry_delay: float = 1.0
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    
    # Monitoring
    enable_metrics: bool = True
    log_slow_queries: bool = True
    slow_query_threshold: float = 1.0


@dataclass
class OperationContext:
    """Context for service operations"""
    operation_type: OperationType
    user_id: Optional[str] = None
    client_id: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class OperationResult(Generic[T]):
    """Result of a service operation"""
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    cache_hit: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class ServiceLayerError(Exception):
    """Base exception for service layer errors"""
    pass


class RateLimitExceededError(ServiceLayerError):
    """Raised when rate limit is exceeded"""
    pass


class DatabaseOverloadError(ServiceLayerError):
    """Raised when database is overloaded"""
    pass


class ValidationError(ServiceLayerError):
    """Raised when validation fails"""
    pass


class CircuitBreakerOpenError(ServiceLayerError):
    """Raised when circuit breaker is open"""
    pass


class RateLimiter:
    """Rate limiter using Redis"""
    
    def __init__(self, redis_client, config: ServiceConfig):
        self.redis = redis_client
        self.config = config
    
    async def check_rate_limit(self, key: str, limit: Optional[int] = None) -> bool:
        """Check if operation is within rate limit"""
        limit = limit or self.config.max_requests_per_minute
        window = 60  # 1 minute window
        
        try:
            current_time = int(datetime.utcnow().timestamp())
            window_start = current_time - window
            
            # Use sliding window rate limiting
            pipe = self.redis.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            pipe.zadd(key, {str(current_time): current_time})
            pipe.expire(key, window)
            
            results = await pipe.execute()
            current_requests = results[1]
            
            return current_requests < limit
            
        except Exception as e:
            logger.warning(f"Rate limiter error: {e}")
            return True  # Fail open


class CircuitBreaker:
    """Circuit breaker pattern implementation"""
    
    def __init__(self, redis_client, config: ServiceConfig):
        self.redis = redis_client
        self.config = config
    
    async def is_open(self, service_name: str) -> bool:
        """Check if circuit breaker is open"""
        try:
            key = f"circuit_breaker:{service_name}"
            failure_count = await self.redis.get(f"{key}:failures")
            last_failure = await self.redis.get(f"{key}:last_failure")
            
            if not failure_count:
                return False
            
            failure_count = int(failure_count)
            if failure_count < self.config.circuit_breaker_threshold:
                return False
            
            if last_failure:
                last_failure_time = datetime.fromisoformat(last_failure)
                if datetime.utcnow() - last_failure_time > timedelta(seconds=self.config.circuit_breaker_timeout):
                    # Reset circuit breaker
                    await self.redis.delete(f"{key}:failures", f"{key}:last_failure")
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Circuit breaker error: {e}")
            return False  # Fail closed
    
    async def record_success(self, service_name: str):
        """Record successful operation"""
        try:
            key = f"circuit_breaker:{service_name}"
            await self.redis.delete(f"{key}:failures")
            await self.redis.delete(f"{key}:last_failure")
        except Exception as e:
            logger.warning(f"Circuit breaker success recording error: {e}")
    
    async def record_failure(self, service_name: str):
        """Record failed operation"""
        try:
            key = f"circuit_breaker:{service_name}"
            pipe = self.redis.pipeline()
            pipe.incr(f"{key}:failures")
            pipe.set(f"{key}:last_failure", datetime.utcnow().isoformat())
            pipe.expire(f"{key}:failures", self.config.circuit_breaker_timeout)
            pipe.expire(f"{key}:last_failure", self.config.circuit_breaker_timeout)
            await pipe.execute()
        except Exception as e:
            logger.warning(f"Circuit breaker failure recording error: {e}")


class CacheManager:
    """Cache management for service layer"""
    
    def __init__(self, redis_client, config: ServiceConfig):
        self.redis = redis_client
        self.config = config
    
    def _get_cache_key(self, prefix: str, *args) -> str:
        """Generate cache key"""
        return f"service_cache:{prefix}:{':'.join(str(arg) for arg in args)}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            cache_key = self._get_cache_key("data", key)
            value = await self.redis.get(cache_key)
            if value:
                import json
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        try:
            cache_key = self._get_cache_key("data", key)
            ttl = ttl or self.config.default_cache_ttl
            import json
            serialized_value = json.dumps(value, default=str)
            await self.redis.setex(cache_key, ttl, serialized_value)
            return True
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            cache_key = self._get_cache_key("data", key)
            await self.redis.delete(cache_key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str) -> bool:
        """Invalidate cache keys matching pattern"""
        try:
            cache_pattern = self._get_cache_key("data", pattern)
            keys = await self.redis.keys(cache_pattern)
            if keys:
                await self.redis.delete(*keys)
            return True
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")
            return False


class BaseService(ABC, Generic[T]):
    """Base service class with common functionality"""
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        self.config = config or ServiceConfig()
        self.rate_limiter = RateLimiter(redis_client, self.config)
        self.circuit_breaker = CircuitBreaker(redis_client, self.config)
        self.cache_manager = CacheManager(redis_client, self.config)
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent_operations)
    
    @property
    @abstractmethod
    def service_name(self) -> str:
        """Service name for monitoring and circuit breaker"""
        pass
    
    async def _check_preconditions(self, context: OperationContext) -> None:
        """Check preconditions before operation"""
        # Rate limiting
        rate_limit_key = f"rate_limit:{self.service_name}:{context.user_id or 'anonymous'}"
        if not await self.rate_limiter.check_rate_limit(rate_limit_key):
            raise RateLimitExceededError(f"Rate limit exceeded for {self.service_name}")
        
        # Circuit breaker
        if await self.circuit_breaker.is_open(self.service_name):
            raise CircuitBreakerOpenError(f"Circuit breaker open for {self.service_name}")
    
    async def _validate_input(self, data: Any, context: OperationContext) -> None:
        """Validate input data"""
        # Override in subclasses for specific validation
        pass
    
    async def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Get data from cache if strategy allows"""
        if self.config.cache_strategy in [CacheStrategy.READ_THROUGH, CacheStrategy.CACHE_ASIDE]:
            return await self.cache_manager.get(cache_key)
        return None
    
    async def _set_cache(self, cache_key: str, data: Any, ttl: Optional[int] = None) -> None:
        """Set data in cache if strategy allows"""
        if self.config.cache_strategy in [
            CacheStrategy.READ_THROUGH, 
            CacheStrategy.WRITE_THROUGH, 
            CacheStrategy.CACHE_ASIDE
        ]:
            await self.cache_manager.set(cache_key, data, ttl)
    
    async def _invalidate_cache(self, pattern: str) -> None:
        """Invalidate cache entries"""
        await self.cache_manager.invalidate_pattern(pattern)
    
    @asynccontextmanager
    async def _get_db_session(self):
        """Get database session with proper error handling"""
        from app.database.connection import get_db_session
        
        async with get_db_session() as db:
            try:
                yield db
            except Exception as e:
                await self.circuit_breaker.record_failure(self.service_name)
                raise
            else:
                await self.circuit_breaker.record_success(self.service_name)
    
    async def execute_operation(
        self,
        operation: Callable,
        context: OperationContext,
        *args,
        **kwargs
    ) -> OperationResult[T]:
        """Execute operation with full service layer protection"""
        start_time = datetime.utcnow()
        
        try:
            # Check preconditions
            await self._check_preconditions(context)
            
            # Acquire semaphore for concurrency control
            async with self._semaphore:
                # Execute operation with retry logic
                for attempt in range(self.config.max_retries + 1):
                    try:
                        result = await operation(*args, **kwargs)
                        
                        execution_time = (datetime.utcnow() - start_time).total_seconds()
                        
                        # Log slow queries
                        if (self.config.log_slow_queries and 
                            execution_time > self.config.slow_query_threshold):
                            logger.warning(
                                f"Slow operation in {self.service_name}: "
                                f"{execution_time:.2f}s, operation: {context.operation_type.value}"
                            )
                        
                        return OperationResult(
                            success=True,
                            data=result,
                            execution_time=execution_time,
                            metadata={"attempts": attempt + 1}
                        )
                        
                    except Exception as e:
                        if attempt == self.config.max_retries:
                            raise
                        
                        # Wait before retry
                        await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
                        logger.warning(f"Retrying operation (attempt {attempt + 1}): {e}")
        
        except RateLimitExceededError as e:
            return OperationResult(success=False, error=str(e))
        except CircuitBreakerOpenError as e:
            return OperationResult(success=False, error=str(e))
        except ValidationError as e:
            return OperationResult(success=False, error=str(e))
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Operation failed in {self.service_name}: {e}")
            return OperationResult(
                success=False,
                error=str(e),
                execution_time=execution_time
            )


# Service layer registry
_service_registry: Dict[str, BaseService] = {}


def register_service(service_name: str, service_instance: BaseService) -> None:
    """Register a service in the global registry"""
    _service_registry[service_name] = service_instance


def get_service(service_name: str) -> Optional[BaseService]:
    """Get a service from the registry"""
    return _service_registry.get(service_name)


def get_all_services() -> Dict[str, BaseService]:
    """Get all registered services"""
    return _service_registry.copy()