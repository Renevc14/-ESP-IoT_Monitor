import json
import logging
from datetime import datetime

import aio_pika
from aio_pika import ExchangeType

from app.config import settings

logger = logging.getLogger(__name__)

_connection: aio_pika.abc.AbstractConnection | None = None
_channel: aio_pika.abc.AbstractChannel | None = None
_exchange: aio_pika.abc.AbstractExchange | None = None


async def connect() -> None:
    global _connection, _channel, _exchange
    _connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    _channel = await _connection.channel()
    _exchange = await _channel.declare_exchange(
        settings.exchange_name,
        ExchangeType.FANOUT,
        durable=True,
    )
    logger.info("RabbitMQ connected — exchange: %s", settings.exchange_name)


async def disconnect() -> None:
    if _connection:
        await _connection.close()
    logger.info("RabbitMQ connection closed")


async def publish(payload: dict) -> None:
    if _exchange is None:
        raise RuntimeError("RabbitMQ exchange not initialized")

    # Serialize datetimes to ISO strings
    body = json.dumps(payload, default=lambda o: o.isoformat() if isinstance(o, datetime) else str(o))
    message = aio_pika.Message(
        body=body.encode(),
        content_type="application/json",
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
    )
    await _exchange.publish(message, routing_key="")
    logger.debug("Published to %s: %s", settings.exchange_name, body[:120])
