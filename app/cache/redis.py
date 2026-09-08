import json
import logging
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class RedisCache:
    def __init__(self, client: Redis | None, ttl: int) -> None:
        self.client, self.ttl = client, ttl

    async def get(self, key: str) -> dict | None:
        if not self.client: return None
        try:
            raw = await self.client.get(key)
            return json.loads(raw) if raw else None
        except Exception:
            logger.warning("cache read unavailable")
            return None

    async def set(self, key: str, value: dict) -> None:
        if not self.client: return
        try:
            await self.client.set(key, json.dumps(value), ex=self.ttl)
        except Exception:
            logger.warning("cache write unavailable")
