from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis

from app.config import settings
from app.middleware.rate_limiter import rate_limit_middleware
from app.middleware.security_headers import security_headers_middleware
from app.proxy import router as proxy_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = Redis.from_url(settings.redis_url, decode_responses=True)
    # Cliente HTTP compartido para el proxy (keep-alive entre peticiones).
    app.state.http = httpx.AsyncClient(timeout=30)
    yield
    await app.state.http.aclose()
    await app.state.redis.aclose()


app = FastAPI(
    title="IoT API Gateway",
    description="Proxy de borde: validación JWT, rate limiting (Redis) y headers de seguridad (OWASP A05). Enruta a identity/registry/alerts.",
    version="2.0.0",
    contact={"name": "Rene Vilela", "email": "rene.vilela@ucb.edu.bo"},
    lifespan=lifespan,
)

origins = [o.strip() for o in settings.allowed_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(security_headers_middleware)
app.middleware("http")(rate_limit_middleware)

_SERVICES = {
    "identity": settings.identity_url,
    "registry": settings.registry_url,
    "ingestion": settings.ingestion_url,
    "processing": settings.processing_url,
    "alerts": settings.alerts_url,
    "analytics": settings.analytics_url,
}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "gateway"}


@app.get("/system/health", tags=["System"])
async def system_health():
    out = [{"service": "gateway", "status": "healthy"}]
    client: httpx.AsyncClient = app.state.http
    for name, url in _SERVICES.items():
        try:
            resp = await client.get(f"{url}/health", timeout=4.0)
            resp.raise_for_status()
            out.append({"service": name, "status": "healthy"})
        except Exception:
            out.append({"service": name, "status": "down"})
    return out


app.include_router(proxy_router)
