from typing import Protocol
from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimiter(Protocol):
    async def allow(self, key: str) -> bool: ...


class RedisTokenBucket:
    SCRIPT = """local b=redis.call('HMGET',KEYS[1],'tokens','updated'); local now=tonumber(ARGV[1]); local cap=tonumber(ARGV[2]); local rate=tonumber(ARGV[3]); local tokens=tonumber(b[1]) or cap; local updated=tonumber(b[2]) or now; tokens=math.min(cap,tokens+(now-updated)*rate); if tokens < 1 then redis.call('HMSET',KEYS[1],'tokens',tokens,'updated',now); redis.call('EXPIRE',KEYS[1],math.ceil(cap/rate)+1); return 0 end; redis.call('HMSET',KEYS[1],'tokens',tokens-1,'updated',now); redis.call('EXPIRE',KEYS[1],math.ceil(cap/rate)+1); return 1"""
    def __init__(self, redis: Redis | None, capacity: int, refill_rate: float) -> None:
        self.redis, self.capacity, self.refill_rate = redis, capacity, refill_rate
    async def allow(self, key: str) -> bool:
        if self.redis is None: return True
        try:
            import time
            return bool(await self.redis.eval(self.SCRIPT, 1, f"rag:rate:{key}", time.time(), self.capacity, self.refill_rate))
        except Exception:
            return True


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limiter: RateLimiter) -> None:
        super().__init__(app); self.limiter = limiter
    async def dispatch(self, request, call_next):
        # The Redis client is lifecycle-owned by the application, not a global.
        if isinstance(self.limiter, RedisTokenBucket):
            self.limiter.redis = getattr(request.app.state, "redis", None)
        if not await self.limiter.allow(request.client.host if request.client else "unknown"):
            return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
        return await call_next(request)
