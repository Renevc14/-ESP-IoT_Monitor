from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis

from app.config import settings
from app.middleware.rate_limiter import rate_limit_middleware
from app.routers import auth, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: connect Redis
    app.state.redis = Redis.from_url(settings.redis_url, decode_responses=True)
    yield
    # Shutdown: close Redis
    await app.state.redis.aclose()


app = FastAPI(
    title="IoT API Gateway",
    description="API Gateway — JWT authentication, RBAC, rate limiting",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
origins = [o.strip() for o in settings.allowed_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware
app.middleware("http")(rate_limit_middleware)

# Routers
app.include_router(auth.router)
app.include_router(users.router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "gateway"}
