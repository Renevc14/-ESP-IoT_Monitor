import pytest

from app.broadcaster import Broadcaster


@pytest.mark.asyncio
async def test_publish_reaches_subscriber():
    b = Broadcaster()
    q = b.subscribe()
    await b.publish({"value": 1})
    assert (await q.get()) == {"value": 1}


@pytest.mark.asyncio
async def test_unsubscribe_stops_delivery():
    b = Broadcaster()
    q = b.subscribe()
    b.unsubscribe(q)
    await b.publish({"value": 2})
    assert q.empty()
