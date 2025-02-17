import redis.asyncio as redis
from datetime import datetime, timedelta
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class StorageService:

    def __init__(self,
                 storage_type: str = "redis",
                 redis_url: Optional[str] = None):
        self.storage_type = storage_type
        if storage_type == "redis":
            self.redis = redis.from_url(redis_url
                                        or "redis://localhost:6379/0")
        else:
            self.memory_storage = {}

    async def close(self):
        if self.storage_type == "redis":
            await self.redis.close()

    async def store_task(self,
                         task_id: str,
                         data: Dict[str, Any],
                         ttl: int = 86400):
        try:
            if self.storage_type == "redis":
                await self.redis.setex(f"task:{task_id}", ttl, str(data))
            else:
                self.memory_storage[task_id] = data
            return True
        except Exception as e:
            logger.error(f"Error storing task {task_id}: {str(e)}")
            return False

    async def cleanup_tasks(self, max_age_hours: int = 24):
        try:
            if self.storage_type == "redis":
                # Redis handles TTL automatically
                pass
            else:
                cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
                self.memory_storage = {
                    k: v
                    for k, v in self.memory_storage.items()
                    if v.get('timestamp', datetime.utcnow()) > cutoff
                }
        except Exception as e:
            logger.error(f"Error during task cleanup: {str(e)}")
