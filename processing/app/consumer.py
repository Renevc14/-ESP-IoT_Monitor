import json
import logging
from datetime import datetime

import aio_pika
from aio_pika import ExchangeType
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.config import settings
from app.models.reading import SensorReading

logger = logging.getLogger(__name__)

_connection: aio_pika.abc.AbstractConnection | None = None


async def _persist_and_cache(message_body: dict, session_factory: async_sessionmaker, redis: Redis) -> None:
    device_id = message_body["device_id"]
    sensor_type = message_body["sensor_type"]
    value = float(message_body["value"])
    unit = message_body["unit"]
    recorded_at = datetime.fromisoformat(message_body["recorded_at"].replace("Z", "+00:00"))

    # Persist to TimescaleDB hypertable
    async with session_factory() as session:
        reading = SensorReading(
            device_id=device_id,
            sensor_type=sensor_type,
            value=value,
            unit=unit,
            recorded_at=recorded_at,
        )
        session.add(reading)
        await session.commit()

    # Cache latest reading in Redis
    cache_key = f"device:{device_id}:latest:{sensor_type}"
    cache_value = json.dumps({
        "value": value,
        "unit": unit,
        "recorded_at": recorded_at.isoformat(),
    })
    await redis.setex(cache_key, settings.redis_cache_ttl, cache_value)

    logger.info("Persisted & cached: device=%s type=%s value=%s%s", device_id, sensor_type, value, unit)


async def start_consuming(session_factory: async_sessionmaker, redis: Redis) -> None:
    global _connection
    _connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    channel = await _connection.channel()
    await channel.set_qos(prefetch_count=10)

    exchange = await channel.declare_exchange(
        settings.exchange_name,
        ExchangeType.FANOUT,
        durable=True,
    )

    # Dead-letter queue: los mensajes que fallan tras un reintento se desvían aquí
    # en vez de perderse (datos sin persistir) o reencolarse en bucle.
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
            try:
                body = json.loads(message.body.decode())
                await _persist_and_cache(body, session_factory, redis)
                await message.ack()
            except Exception as exc:
                # Primer fallo: reintentar (transitorio). Segundo: a la DLQ (veneno).
                requeue = not message.redelivered
                logger.error(
                    "Failed to process message (requeue=%s): %s | body: %s",
                    requeue, exc, message.body[:200],
                )
                await message.nack(requeue=requeue)


async def stop_consuming() -> None:
    if _connection:
        await _connection.close()
    logger.info("Processing consumer stopped")
