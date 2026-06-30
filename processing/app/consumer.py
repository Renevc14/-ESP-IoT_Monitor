import json
import logging
from datetime import datetime

import aio_pika
from aio_pika import ExchangeType
from pydantic import BaseModel, Field, ValidationError
from redis.asyncio import Redis
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.config import settings
from app.models.reading import SensorReading

logger = logging.getLogger(__name__)

_connection: aio_pika.abc.AbstractConnection | None = None


class _IncomingReading(BaseModel):
    """Contrato del mensaje en el consumidor: valida formato antes de persistir."""
    device_id: str
    sensor_type: str
    value: float = Field(allow_inf_nan=False)
    unit: str
    recorded_at: datetime


async def _persist_and_cache(reading: _IncomingReading, session_factory: async_sessionmaker, redis: Redis) -> None:
    # Idempotente: ON CONFLICT DO NOTHING evita filas duplicadas si el mensaje se
    # reentrega (semántica at-least-once); la clave natural es (device, sensor, recorded_at).
    async with session_factory() as session:
        stmt = (
            pg_insert(SensorReading.__table__)
            .values(
                device_id=reading.device_id,
                sensor_type=reading.sensor_type,
                value=reading.value,
                unit=reading.unit,
                recorded_at=reading.recorded_at,
            )
            .on_conflict_do_nothing(index_elements=["device_id", "sensor_type", "recorded_at"])
        )
        await session.execute(stmt)
        await session.commit()

    cache_key = f"device:{reading.device_id}:latest:{reading.sensor_type}"
    cache_value = json.dumps({
        "value": reading.value,
        "unit": reading.unit,
        "recorded_at": reading.recorded_at.isoformat(),
    })
    await redis.setex(cache_key, settings.redis_cache_ttl, cache_value)
    logger.info(
        "Persisted & cached: device=%s type=%s value=%s%s",
        reading.device_id, reading.sensor_type, reading.value, reading.unit,
    )


async def handle_message(message, session_factory: async_sessionmaker, redis: Redis) -> None:
    """Procesa un mensaje distinguiendo error permanente (veneno) de transitorio.

    Formato inválido (JSON/validación) → DLQ inmediata, no se reintenta.
    Éxito → ack (idempotente). Fallo transitorio (BD/Redis) → reintento y luego DLQ.
    """
    try:
        body = json.loads(message.body.decode())
        reading = _IncomingReading.model_validate(body)
    except (json.JSONDecodeError, ValidationError) as exc:
        logger.error("Mensaje inválido descartado a DLQ: %s | body: %s", exc, message.body[:200])
        await message.nack(requeue=False)
        return

    try:
        await _persist_and_cache(reading, session_factory, redis)
        await message.ack()
    except Exception as exc:
        requeue = not message.redelivered
        logger.error("Fallo transitorio al procesar (requeue=%s): %s", requeue, exc)
        await message.nack(requeue=requeue)


async def start_consuming(session_factory: async_sessionmaker, redis: Redis) -> None:  # pragma: no cover
    global _connection
    _connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    channel = await _connection.channel()
    await channel.set_qos(prefetch_count=10)

    exchange = await channel.declare_exchange(
        settings.exchange_name,
        ExchangeType.FANOUT,
        durable=True,
    )

    # Dead-letter queue: los mensajes que fallan se desvían aquí en vez de perderse.
    dlx_name = f"{settings.queue_name}.dlx"
    dlx = await channel.declare_exchange(dlx_name, ExchangeType.FANOUT, durable=True)
    dlq = await channel.declare_queue(f"{settings.queue_name}.dlq", durable=True)
    await dlq.bind(dlx)

    queue = await channel.declare_queue(
        settings.queue_name,
        durable=True,
        arguments={"x-dead-letter-exchange": dlx_name},
    )
    await queue.bind(exchange)

    logger.info("Processing consumer started — queue: %s", settings.queue_name)

    async with queue.iterator() as q:
        async for message in q:
            await handle_message(message, session_factory, redis)


async def stop_consuming() -> None:  # pragma: no cover
    if _connection:
        await _connection.close()
    logger.info("Processing consumer stopped")
