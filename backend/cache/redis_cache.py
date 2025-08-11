#!/usr/bin/env python3
"""
Redis Caching Service for ProxyAssessmentTool
High-performance caching layer with pub/sub support
"""

import asyncio
import json
import logging
import pickle
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Union
from uuid import UUID

import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class RedisCache:
    """Production-grade Redis caching service"""
    
    # Cache key prefixes
    PROXY_PREFIX = "proxy:"
    TEST_PREFIX = "test:"
    STATS_PREFIX = "stats:"
    BLACKLIST_PREFIX = "blacklist:"
    QUEUE_PREFIX = "queue:"
    LOCK_PREFIX = "lock:"
    
    # Default TTLs (in seconds)
    PROXY_TTL = 3600  # 1 hour
    TEST_TTL = 86400  # 24 hours
    STATS_TTL = 300   # 5 minutes
    BLACKLIST_TTL = 300  # 5 minutes
    
    def __init__(self, 
                 redis_url: str = "redis://localhost:6379/0",
                 max_connections: int = 50,
                 decode_responses: bool = False):
        """
        Initialize Redis cache
        
        Args:
            redis_url: Redis connection URL
            max_connections: Maximum pool connections
            decode_responses: Whether to decode responses as strings
        """
        self.redis_url = redis_url
        self.pool = ConnectionPool.from_url(
            redis_url,
            max_connections=max_connections,
            decode_responses=decode_responses,
            health_check_interval=30
        )
        self.redis: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self._subscribers = {}
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis = redis.Redis(connection_pool=self.pool)
            await self.redis.ping()
            logger.info("Connected to Redis")
            
            # Initialize pub/sub
            self.pubsub = self.redis.pubsub()
            
        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.pubsub:
            await self.pubsub.close()
        if self.redis:
            await self.redis.close()
        await self.pool.disconnect()
        logger.info("Disconnected from Redis")
    
    # Basic cache operations
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = await self.redis.get(key)
            if value:
                return self._deserialize(value)
            return None
        except RedisError as e:
            logger.error(f"Redis GET error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL"""
        try:
            serialized = self._serialize(value)
            if ttl:
                await self.redis.setex(key, ttl, serialized)
            else:
                await self.redis.set(key, serialized)
            return True
        except RedisError as e:
            logger.error(f"Redis SET error for key {key}: {e}")
            return False
    
    async def delete(self, *keys: str) -> int:
        """Delete keys from cache"""
        try:
            if keys:
                return await self.redis.delete(*keys)
            return 0
        except RedisError as e:
            logger.error(f"Redis DELETE error: {e}")
            return 0
    
    async def exists(self, *keys: str) -> int:
        """Check if keys exist"""
        try:
            return await self.redis.exists(*keys)
        except RedisError as e:
            logger.error(f"Redis EXISTS error: {e}")
            return 0
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration time for key"""
        try:
            return await self.redis.expire(key, seconds)
        except RedisError as e:
            logger.error(f"Redis EXPIRE error for key {key}: {e}")
            return False
    
    # Proxy-specific cache methods
    
    async def cache_proxy(self, proxy_id: Union[str, UUID], proxy_data: Dict[str, Any], ttl: int = None) -> bool:
        """Cache proxy data"""
        key = f"{self.PROXY_PREFIX}{proxy_id}"
        ttl = ttl or self.PROXY_TTL
        return await self.set(key, proxy_data, ttl)
    
    async def get_proxy(self, proxy_id: Union[str, UUID]) -> Optional[Dict[str, Any]]:
        """Get cached proxy data"""
        key = f"{self.PROXY_PREFIX}{proxy_id}"
        return await self.get(key)
    
    async def cache_proxy_batch(self, proxies: List[Dict[str, Any]], ttl: int = None) -> int:
        """Cache multiple proxies in batch"""
        ttl = ttl or self.PROXY_TTL
        pipeline = self.redis.pipeline()
        
        for proxy in proxies:
            proxy_id = proxy.get('id')
            if proxy_id:
                key = f"{self.PROXY_PREFIX}{proxy_id}"
                serialized = self._serialize(proxy)
                pipeline.setex(key, ttl, serialized)
        
        try:
            results = await pipeline.execute()
            return sum(1 for r in results if r)
        except RedisError as e:
            logger.error(f"Redis batch cache error: {e}")
            return 0
    
    async def cache_test_result(self, test_id: Union[str, UUID], result: Dict[str, Any], ttl: int = None) -> bool:
        """Cache test result"""
        key = f"{self.TEST_PREFIX}{test_id}"
        ttl = ttl or self.TEST_TTL
        return await self.set(key, result, ttl)
    
    async def get_test_result(self, test_id: Union[str, UUID]) -> Optional[Dict[str, Any]]:
        """Get cached test result"""
        key = f"{self.TEST_PREFIX}{test_id}"
        return await self.get(key)
    
    # Statistics caching
    
    async def increment_counter(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a counter"""
        try:
            return await self.redis.incrby(key, amount)
        except RedisError as e:
            logger.error(f"Redis INCRBY error for key {key}: {e}")
            return None
    
    async def get_counter(self, key: str) -> int:
        """Get counter value"""
        try:
            value = await self.redis.get(key)
            return int(value) if value else 0
        except (RedisError, ValueError) as e:
            logger.error(f"Redis counter error for key {key}: {e}")
            return 0
    
    async def cache_stats(self, stats_type: str, stats: Dict[str, Any], ttl: int = None) -> bool:
        """Cache statistics"""
        key = f"{self.STATS_PREFIX}{stats_type}"
        ttl = ttl or self.STATS_TTL
        return await self.set(key, stats, ttl)
    
    async def get_stats(self, stats_type: str) -> Optional[Dict[str, Any]]:
        """Get cached statistics"""
        key = f"{self.STATS_PREFIX}{stats_type}"
        return await self.get(key)
    
    # Blacklist caching
    
    async def add_to_blacklist(self, ip: str, port: Optional[int] = None, ttl: int = None) -> bool:
        """Add IP/port to blacklist cache"""
        key = f"{self.BLACKLIST_PREFIX}{ip}:{port or '*'}"
        ttl = ttl or self.BLACKLIST_TTL
        return await self.set(key, True, ttl)
    
    async def is_blacklisted(self, ip: str, port: Optional[int] = None) -> bool:
        """Check if IP/port is in blacklist cache"""
        # Check specific port
        if port:
            key = f"{self.BLACKLIST_PREFIX}{ip}:{port}"
            if await self.exists(key):
                return True
        
        # Check all ports
        key = f"{self.BLACKLIST_PREFIX}{ip}:*"
        return bool(await self.exists(key))
    
    async def remove_from_blacklist(self, ip: str, port: Optional[int] = None) -> bool:
        """Remove IP/port from blacklist cache"""
        key = f"{self.BLACKLIST_PREFIX}{ip}:{port or '*'}"
        return bool(await self.delete(key))
    
    # Queue operations
    
    async def push_to_queue(self, queue_name: str, *items: Any) -> int:
        """Push items to queue (FIFO)"""
        key = f"{self.QUEUE_PREFIX}{queue_name}"
        try:
            serialized = [self._serialize(item) for item in items]
            return await self.redis.lpush(key, *serialized)
        except RedisError as e:
            logger.error(f"Redis queue push error: {e}")
            return 0
    
    async def pop_from_queue(self, queue_name: str, count: int = 1) -> List[Any]:
        """Pop items from queue"""
        key = f"{self.QUEUE_PREFIX}{queue_name}"
        items = []
        
        try:
            pipeline = self.redis.pipeline()
            for _ in range(count):
                pipeline.rpop(key)
            
            results = await pipeline.execute()
            for result in results:
                if result:
                    items.append(self._deserialize(result))
            
            return items
        except RedisError as e:
            logger.error(f"Redis queue pop error: {e}")
            return []
    
    async def get_queue_size(self, queue_name: str) -> int:
        """Get queue size"""
        key = f"{self.QUEUE_PREFIX}{queue_name}"
        try:
            return await self.redis.llen(key)
        except RedisError as e:
            logger.error(f"Redis queue size error: {e}")
            return 0
    
    # Distributed locking
    
    async def acquire_lock(self, resource: str, timeout: int = 10, blocking: bool = True) -> Optional[str]:
        """
        Acquire distributed lock
        
        Args:
            resource: Resource name to lock
            timeout: Lock timeout in seconds
            blocking: Whether to block waiting for lock
            
        Returns:
            Lock token if acquired, None otherwise
        """
        key = f"{self.LOCK_PREFIX}{resource}"
        token = f"{datetime.utcnow().timestamp()}:{id(self)}"
        
        try:
            if blocking:
                # Try to acquire lock with retries
                for _ in range(timeout * 10):  # Try for timeout seconds
                    if await self.redis.set(key, token, nx=True, ex=timeout):
                        return token
                    await asyncio.sleep(0.1)
            else:
                # Single attempt
                if await self.redis.set(key, token, nx=True, ex=timeout):
                    return token
            
            return None
        except RedisError as e:
            logger.error(f"Redis lock acquire error: {e}")
            return None
    
    async def release_lock(self, resource: str, token: str) -> bool:
        """Release distributed lock"""
        key = f"{self.LOCK_PREFIX}{resource}"
        
        # Lua script to atomically check and delete
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        
        try:
            result = await self.redis.eval(lua_script, 1, key, token)
            return bool(result)
        except RedisError as e:
            logger.error(f"Redis lock release error: {e}")
            return False
    
    # Pub/Sub operations
    
    async def publish(self, channel: str, message: Any) -> int:
        """Publish message to channel"""
        try:
            serialized = self._serialize(message)
            return await self.redis.publish(channel, serialized)
        except RedisError as e:
            logger.error(f"Redis publish error: {e}")
            return 0
    
    async def subscribe(self, channel: str, callback: callable):
        """Subscribe to channel with callback"""
        if channel not in self._subscribers:
            await self.pubsub.subscribe(channel)
            self._subscribers[channel] = callback
            
            # Start listener if not running
            if not hasattr(self, '_listener_task') or self._listener_task.done():
                self._listener_task = asyncio.create_task(self._listen_messages())
    
    async def unsubscribe(self, channel: str):
        """Unsubscribe from channel"""
        if channel in self._subscribers:
            await self.pubsub.unsubscribe(channel)
            del self._subscribers[channel]
    
    async def _listen_messages(self):
        """Listen for pub/sub messages"""
        try:
            async for message in self.pubsub.listen():
                if message['type'] == 'message':
                    channel = message['channel'].decode() if isinstance(message['channel'], bytes) else message['channel']
                    
                    if channel in self._subscribers:
                        try:
                            data = self._deserialize(message['data'])
                            callback = self._subscribers[channel]
                            
                            # Run callback
                            if asyncio.iscoroutinefunction(callback):
                                await callback(data)
                            else:
                                callback(data)
                        except Exception as e:
                            logger.error(f"Pub/sub callback error: {e}")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Pub/sub listener error: {e}")
    
    # Utility methods
    
    async def clear_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        try:
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                return await self.redis.delete(*keys)
            return 0
        except RedisError as e:
            logger.error(f"Redis clear pattern error: {e}")
            return 0
    
    async def get_info(self) -> Dict[str, Any]:
        """Get Redis server info"""
        try:
            info = await self.redis.info()
            return {
                'version': info.get('redis_version'),
                'connected_clients': info.get('connected_clients'),
                'used_memory_human': info.get('used_memory_human'),
                'total_commands_processed': info.get('total_commands_processed'),
                'uptime_in_days': info.get('uptime_in_days')
            }
        except RedisError as e:
            logger.error(f"Redis info error: {e}")
            return {}
    
    def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage"""
        if isinstance(value, (str, int, float, bool)):
            return json.dumps(value).encode()
        elif isinstance(value, UUID):
            return str(value).encode()
        else:
            # Use pickle for complex objects
            return pickle.dumps(value)
    
    def _deserialize(self, value: bytes) -> Any:
        """Deserialize value from storage"""
        try:
            # Try JSON first
            return json.loads(value.decode())
        except:
            try:
                # Fall back to pickle
                return pickle.loads(value)
            except:
                # Last resort - return as string
                return value.decode()


# Singleton instance
_redis_cache: Optional[RedisCache] = None


async def get_redis_cache(redis_url: str = "redis://localhost:6379/0") -> RedisCache:
    """Get or create Redis cache instance"""
    global _redis_cache
    if _redis_cache is None:
        _redis_cache = RedisCache(redis_url)
        await _redis_cache.connect()
    return _redis_cache