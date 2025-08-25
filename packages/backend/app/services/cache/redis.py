"""Redis cache service"""

import json
import pickle
from typing import Any, Optional, Union
import redis.asyncio as redis
import logging

from app.config import settings
from app.core.exceptions import CacheError

logger = logging.getLogger(__name__)


class RedisClient:
    """Async Redis client wrapper"""
    
    def __init__(self):
        self._client: Optional[redis.Redis] = None
    
    @property
    def client(self) -> redis.Redis:
        """Get or create Redis client"""
        if self._client is None:
            self._client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=False  # We'll handle encoding ourselves
            )
        return self._client
    
    async def ping(self) -> bool:
        """Test Redis connection"""
        try:
            await self.client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False
    
    async def close(self):
        """Close Redis connection"""
        if self._client:
            await self._client.close()
            self._client = None
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = await self.client.get(key)
            if value is None:
                return None
            
            # Try JSON first, then pickle
            try:
                return json.loads(value.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return pickle.loads(value)
                
        except Exception as e:
            logger.error(f"Cache get failed for key {key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        expire: Optional[int] = None
    ) -> bool:
        """Set value in cache"""
        try:
            # Try JSON first, fallback to pickle
            try:
                serialized = json.dumps(value, default=str).encode('utf-8')
            except (TypeError, ValueError):
                serialized = pickle.dumps(value)
            
            if expire is None:
                expire = settings.CACHE_TTL
            
            await self.client.set(key, serialized, ex=expire)
            return True
            
        except Exception as e:
            logger.error(f"Cache set failed for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete failed for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            result = await self.client.exists(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Cache exists check failed for key {key}: {e}")
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for key"""
        try:
            await self.client.expire(key, seconds)
            return True
        except Exception as e:
            logger.error(f"Cache expire failed for key {key}: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear keys matching pattern"""
        try:
            keys = await self.client.keys(pattern)
            if keys:
                return await self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern failed for {pattern}: {e}")
            return 0
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter"""
        try:
            return await self.client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Cache increment failed for key {key}: {e}")
            raise CacheError(f"Failed to increment {key}")
    
    async def set_hash(self, key: str, mapping: dict, expire: Optional[int] = None) -> bool:
        """Set hash in cache"""
        try:
            await self.client.hset(key, mapping=mapping)
            if expire:
                await self.client.expire(key, expire)
            return True
        except Exception as e:
            logger.error(f"Cache hash set failed for key {key}: {e}")
            return False
    
    async def get_hash(self, key: str, field: Optional[str] = None) -> Optional[Union[dict, str]]:
        """Get hash from cache"""
        try:
            if field:
                return await self.client.hget(key, field)
            else:
                return await self.client.hgetall(key)
        except Exception as e:
            logger.error(f"Cache hash get failed for key {key}: {e}")
            return None


# Global client instance
redis_client = RedisClient()