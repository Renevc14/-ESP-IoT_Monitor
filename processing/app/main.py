import asyncio
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app import consumer
from app.config import settings
from app.observability import setup_observability

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    redis = Redis.from_url(settings.redis_url, decode_responses=True)

    app.state.redis = redis
    app.state.consumer_ok = False

    # Supervisa el consumidor: si falla al arrancar o se cae el canal, reintenta
    # con backoff en vez de morir en silencio (la Task quedaba sin observar).
    async def _supervise():
        while True:
            try:
                app.state.consumer_ok = True
                await consumer.start_consuming(session_factory, redis)
                app.state.consumer_ok = False  # el iterator terminó inesperadamente
            except asyncio.CancelledError:
                raise
            except Exception:
                app.state.consumer_ok = False
                logger.exception("Consumidor caído; reintentando en 5s")
                await asyncio.sleep(5)

    consume_task = asyncio.create_task(_supervise())

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

setup_observability(app, "processing")


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "processing", "consumer": getattr(app.state, "consumer_ok", False)}


@app.get("/cache/{device_id}/{sensor_type}", tags=["Cache"])
async def get_cached(device_id: str, sensor_type: str):
    """Return the latest cached reading for a device+sensor from Redis."""
    redis: Redis = app.state.redis
    key = f"device:{device_id}:latest:{sensor_type}"
    value = await redis.get(key)
    if value is None:
        return {"cached": False}
    return {"cached": True, "data": json.loads(value)}
