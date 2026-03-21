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
    queue = await channel.declare_queue(settings.queue_name, durable=True)
    await queue.bind(exchange)

    logger.info("Alerts consumer started — queue: %s", settings.queue_name)

    async with queue.iterator() as q:
        async for message in q:
            async with message.process():
                try:
                    body = json.loads(message.body.decode())
                    await evaluate(body, session_factory)
                except Exception as exc:
                    logger.error("Failed to evaluate message: %s", exc)


async def stop_consuming() -> None:
    if _connection:
        await _connection.close()
