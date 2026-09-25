import json
from typing import Any, Optional
import redis.asyncio as redis
from config import settings
import logging

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self):
        self.redis_client = None
        if settings.REDIS_URL:
            try:
                self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")

    async def get(self, key: str) -> Optional[Any]:
        if not self.redis_client:
            return None
        try:
            val = await self.redis_client.get(key)
            if val:
                return json.loads(val)
            return None
        except Exception as e:
            logger.warning(f"Redis get failed for {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        if not self.redis_client:
            return False
        try:
            await self.redis_client.setex(key, ttl, json.dumps(value))
            return True
        except Exception as e:
            logger.warning(f"Redis set failed for {key}: {e}")
            return False

    async def invalidate(self, key: str) -> bool:
        if not self.redis_client:
            return False
        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Redis delete failed for {key}: {e}")
            return False

cache_service = CacheService()
