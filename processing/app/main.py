import asyncio
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app import consumer
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    redis = Redis.from_url(settings.redis_url, decode_responses=True)

    app.state.redis = redis

    # Start AMQP consumer in background task
    consume_task = asyncio.create_task(consumer.start_consuming(session_factory, redis))

    yield

    consume_task.cancel()
    try:
        await consume_task
    except asyncio.CancelledError:
        pass

    await consumer.stop_consuming()
    await redis.aclose()
    await engine.dispose()


app = FastAPI(
    title="IoT Processing Service",
    description="Consumes RabbitMQ messages, persists to TimescaleDB, caches in Redis",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "processing"}


@app.get("/cache/{device_id}/{sensor_type}", tags=["Cache"])
async def get_cached(device_id: str, sensor_type: str):
    """Return the latest cached reading for a device+sensor from Redis."""
    redis: Redis = app.state.redis
    key = f"device:{device_id}:latest:{sensor_type}"
    value = await redis.get(key)
    if value is None:
        return {"cached": False}
    return {"cached": True, "data": json.loads(value)}
