"""
Cache Queue Adapter

Provides a unified interface for cache and queue operations, translating between
the Gateway's API and backend implementations (Redis, etc.).

Usage:
    adapter = CacheQueueAdapter()
    await adapter.initialize()
    
    await adapter.set("key", "value", ttl=3600)
    value = await adapter.get("key")
    await adapter.publish("channel", message)
"""

import json
import time
from typing import Optional, Any, List, Dict

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("Warning: redis package not available")

from services.asset_manager import get_asset_manager, Asset
from config import REDIS_URL


class CacheQueueAdapter:
    """
    Adapter for cache-queue interface.
    
    Provides caching, key-value storage, and pub/sub messaging
    through a consistent API.
    """
    
    def __init__(self):
        self._asset: Optional[Asset] = None
        self._client: Optional[Any] = None
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Initialize the adapter with the bound cache/queue asset."""
        try:
            manager = await get_asset_manager()
            self._asset = manager.get_bound_asset("cache-queue")
            
            # Even if no explicit asset, try to connect to Redis
            if REDIS_AVAILABLE:
                self._client = redis.from_url(REDIS_URL, decode_responses=True)
                # Test connection
                await self._client.ping()
                self._initialized = True
                asset_name = self._asset.asset_id if self._asset else "redis (default)"
                print(f"CacheQueueAdapter initialized with: {asset_name}")
                return True
            else:
                print("CacheQueueAdapter: Redis not available")
                return False
        except Exception as e:
            print(f"CacheQueueAdapter initialization failed: {e}")
            return False
    
    def is_initialized(self) -> bool:
        return self._initialized
    
    def get_asset(self) -> Optional[Asset]:
        return self._asset
    
    # --- Cache Operations ---
    
    async def get(self, key: str) -> Optional[str]:
        """Get a value by key."""
        if not self._initialized:
            return None
        try:
            return await self._client.get(key)
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: str,
        ttl: Optional[int] = None
    ) -> bool:
        """Set a value with optional TTL (seconds)."""
        if not self._initialized:
            return False
        try:
            if ttl:
                await self._client.setex(key, ttl, value)
            else:
                await self._client.set(key, value)
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete a key."""
        if not self._initialized:
            return False
        try:
            await self._client.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        if not self._initialized:
            return False
        try:
            return await self._client.exists(key) > 0
        except Exception as e:
            print(f"Cache exists error: {e}")
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on a key."""
        if not self._initialized:
            return False
        try:
            return await self._client.expire(key, seconds)
        except Exception as e:
            print(f"Cache expire error: {e}")
            return False
    
    # --- JSON Operations ---
    
    async def get_json(self, key: str) -> Optional[Any]:
        """Get and parse JSON value."""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except:
                return value
        return None
    
    async def set_json(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set JSON value."""
        try:
            json_str = json.dumps(value)
            return await self.set(key, json_str, ttl)
        except Exception as e:
            print(f"Cache set_json error: {e}")
            return False
    
    # --- Hash Operations ---
    
    async def hget(self, name: str, key: str) -> Optional[str]:
        """Get hash field."""
        if not self._initialized:
            return None
        try:
            return await self._client.hget(name, key)
        except Exception as e:
            print(f"Cache hget error: {e}")
            return None
    
    async def hset(self, name: str, key: str, value: str) -> bool:
        """Set hash field."""
        if not self._initialized:
            return False
        try:
            await self._client.hset(name, key, value)
            return True
        except Exception as e:
            print(f"Cache hset error: {e}")
            return False
    
    async def hgetall(self, name: str) -> Dict[str, str]:
        """Get all hash fields."""
        if not self._initialized:
            return {}
        try:
            return await self._client.hgetall(name)
        except Exception as e:
            print(f"Cache hgetall error: {e}")
            return {}
    
    # --- Pub/Sub ---
    
    async def publish(self, channel: str, message: str) -> int:
        """Publish message to channel. Returns number of subscribers."""
        if not self._initialized:
            return 0
        try:
            return await self._client.publish(channel, message)
        except Exception as e:
            print(f"Publish error: {e}")
            return 0
    
    # --- Queue Operations ---
    
    async def lpush(self, key: str, *values: str) -> int:
        """Push values to left of list."""
        if not self._initialized:
            return 0
        try:
            return await self._client.lpush(key, *values)
        except Exception as e:
            print(f"Queue lpush error: {e}")
            return 0
    
    async def rpop(self, key: str) -> Optional[str]:
        """Pop from right of list."""
        if not self._initialized:
            return None
        try:
            return await self._client.rpop(key)
        except Exception as e:
            print(f"Queue rpop error: {e}")
            return None
    
    async def llen(self, key: str) -> int:
        """Get list length."""
        if not self._initialized:
            return 0
        try:
            return await self._client.llen(key)
        except Exception as e:
            print(f"Queue llen error: {e}")
            return 0
    
    # --- Health ---
    
    async def health_check(self) -> bool:
        """Check if cache is healthy."""
        if not self._initialized:
            return False
        try:
            await self._client.ping()
            return True
        except:
            return False
    
    async def close(self):
        """Close the Redis connection."""
        if self._client:
            await self._client.close()


# Singleton instance
_adapter: Optional[CacheQueueAdapter] = None


async def get_cache_queue_adapter() -> CacheQueueAdapter:
    """Get or create the singleton CacheQueueAdapter instance."""
    global _adapter
    if _adapter is None:
        _adapter = CacheQueueAdapter()
        await _adapter.initialize()
    return _adapter
