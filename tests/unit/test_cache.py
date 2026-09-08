import pytest
from app.cache.redis import RedisCache

class FakeRedis:
    def __init__(self): self.values = {}; self.fail = False
    async def get(self, key):
        if self.fail: raise ConnectionError
        return self.values.get(key)
    async def set(self, key, value, ex):
        if self.fail: raise ConnectionError
        self.values[key] = value

@pytest.mark.asyncio
async def test_cache_hit_and_miss():
    cache = RedisCache(FakeRedis(), 10)
    assert await cache.get("missing") is None
    await cache.set("present", {"answer": "yes"})
    assert await cache.get("present") == {"answer": "yes"}

@pytest.mark.asyncio
async def test_cache_failure_is_non_fatal():
    redis = FakeRedis(); redis.fail = True
    cache = RedisCache(redis, 10)
    assert await cache.get("x") is None
    await cache.set("x", {})
