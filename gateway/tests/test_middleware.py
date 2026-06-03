"""Unit tests for gateway middlewares (security headers + rate limiter)."""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.middleware.rate_limiter import RateLimiter, rate_limit_middleware
from app.middleware.security_headers import SECURITY_HEADERS, security_headers_middleware


class FakeHeaders(dict):
    def setdefault(self, k, v):  # mimic Starlette headers API used by middleware
        return super().setdefault(k, v)


@pytest.mark.asyncio
async def test_security_headers_added():
    response = SimpleNamespace(headers=FakeHeaders())

    async def call_next(_req):
        return response

    out = await security_headers_middleware(SimpleNamespace(), call_next)
    for header in SECURITY_HEADERS:
        assert header in out.headers
    assert out.headers["X-Frame-Options"] == "DENY"


class FakePipe:
    def __init__(self, count):
        self._count = count

    def zremrangebyscore(self, *a, **k): return self
    def zadd(self, *a, **k): return self
    def zcard(self, *a, **k): return self
    def expire(self, *a, **k): return self

    async def execute(self):
        return [0, 1, self._count, True]


class FakeRedis:
    def __init__(self, count):
        self._count = count

    def pipeline(self):
        return FakePipe(self._count)


@pytest.mark.asyncio
async def test_rate_limiter_allows_under_limit():
    await RateLimiter(FakeRedis(5), limit=100).check("rate:1.2.3.4")  # no raise


@pytest.mark.asyncio
async def test_rate_limiter_blocks_over_limit():
    with pytest.raises(HTTPException) as exc:
        await RateLimiter(FakeRedis(101), limit=100).check("rate:1.2.3.4")
    assert exc.value.status_code == 429


@pytest.mark.asyncio
async def test_rate_limit_middleware_passthrough_without_redis():
    called = {}

    async def call_next(_req):
        called["yes"] = True
        return "ok"

    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace()), client=SimpleNamespace(host="1.2.3.4"))
    assert await rate_limit_middleware(request, call_next) == "ok"
    assert called["yes"]


@pytest.mark.asyncio
async def test_rate_limit_middleware_with_redis_ok():
    request = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(redis=FakeRedis(1))),
        client=SimpleNamespace(host="9.9.9.9"),
    )

    async def call_next(_req):
        return "ok"

    assert await rate_limit_middleware(request, call_next) == "ok"
