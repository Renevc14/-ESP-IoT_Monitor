import time

from fastapi import HTTPException, Request, status
from redis.asyncio import Redis


class RateLimiter:
    def __init__(self, redis: Redis, limit: int = 100, window: int = 60):
        self.redis = redis
        self.limit = limit
        self.window = window

    async def check(self, key: str) -> None:
        now = int(time.time())
        window_start = now - self.window
        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, self.window)
        results = await pipe.execute()
        count = results[2]
        if count > self.limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Try again in a minute.",
            )


async def rate_limit_middleware(request: Request, call_next):
    redis: Redis | None = getattr(request.app.state, "redis", None)
    if redis:
        ip = request.client.host if request.client else "unknown"
        limiter = RateLimiter(redis)
        await limiter.check(f"rate:{ip}")
    return await call_next(request)
