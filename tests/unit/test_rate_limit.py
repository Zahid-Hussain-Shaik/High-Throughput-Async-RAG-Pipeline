import pytest
from app.middleware.rate_limit import RedisTokenBucket

class FakeRedis:
    def __init__(self, values): self.values = iter(values)
    async def eval(self, *args): return next(self.values)

@pytest.mark.asyncio
async def test_token_available():
    assert await RedisTokenBucket(FakeRedis([1]), 2, 1).allow("client")

@pytest.mark.asyncio
async def test_token_exhausted():
    assert not await RedisTokenBucket(FakeRedis([0]), 2, 1).allow("client")

@pytest.mark.asyncio
async def test_redis_failure_fails_open():
    class Broken:
        async def eval(self, *args): raise ConnectionError
    assert await RedisTokenBucket(Broken(), 2, 1).allow("client")
