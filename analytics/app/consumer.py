"""Consumes the sensor fanout exchange and forwards readings to the broadcaster
so GraphQL subscriptions can stream them in real time."""
import json
import logging

import aio_pika
from aio_pika import ExchangeType

from app.broadcaster import broadcaster
from app.config import settings

logger = logging.getLogger(__name__)

_connection: aio_pika.abc.AbstractConnection | None = None


async def start_consuming() -> None:
    global _connection
    _connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    channel = await _connection.channel()
    await channel.set_qos(prefetch_count=20)

    exchange = await channel.declare_exchange(settings.exchange_name, ExchangeType.FANOUT, durable=True)
    # Cola exclusiva y efímera (nombre generado por el broker): así CADA instancia de
    # analytics recibe TODAS las lecturas (no hay competing-consumers entre réplicas),
    # de modo que las suscripciones GraphQL funcionan con escalado horizontal (RNF-06).
    queue = await channel.declare_queue(exclusive=True, auto_delete=True)
    await queue.bind(exchange)

    logger.info("Analytics consumer started — queue: %s", settings.queue_name)

    async with queue.iterator() as q:
        async for message in q:
            async with message.process():
                try:
                    body = json.loads(message.body.decode())
                    await broadcaster.publish(body)
                except Exception as exc:
                    logger.error("Failed to forward reading: %s", exc)


async def stop_consuming() -> None:
    if _connection:
        await _connection.close()
