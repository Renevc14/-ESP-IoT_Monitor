import json
import logging

import aio_pika
from aio_pika import ExchangeType
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.config import settings
from app.evaluator import evaluate

logger = logging.getLogger(__name__)

_connection: aio_pika.abc.AbstractConnection | None = None


async def start_consuming(session_factory: async_sessionmaker) -> None:
    global _connection
    _connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    channel = await _connection.channel()
    await channel.set_qos(prefetch_count=10)

    exchange = await channel.declare_exchange(
        settings.exchange_name, ExchangeType.FANOUT, durable=True,
    )

    # Dead-letter queue: evita perder o reencolar en bucle los mensajes que fallan.
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

    logger.info("Alerts consumer started — queue: %s", settings.queue_name)

    async with queue.iterator() as q:
        async for message in q:
            try:
                body = json.loads(message.body.decode())
                await evaluate(body, session_factory)
                await message.ack()
            except Exception as exc:
                # Primer fallo: reintentar (transitorio). Segundo: a la DLQ (veneno).
                requeue = not message.redelivered
                logger.error("Failed to evaluate message (requeue=%s): %s", requeue, exc)
                await message.nack(requeue=requeue)


async def stop_consuming() -> None:
    if _connection:
        await _connection.close()
