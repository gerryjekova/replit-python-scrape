import redis.asyncio as redis
import logging
from ..core.config import settings

logger = logging.getLogger(__name__)


class RedisService:

    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self._redis = None

    async def get_redis(self) -> redis.Redis:
        if self._redis is None:
            try:
                self._redis = redis.from_url(self.redis_url,
                                             encoding="utf-8",
                                             decode_responses=True)
                await self._redis.ping()
                logger.info("Redis connection established")
            except Exception as e:
                logger.error(f"Redis connection failed: {str(e)}")
                raise
        return self._redis

    async def close(self):
        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.info("Redis connection closed")
