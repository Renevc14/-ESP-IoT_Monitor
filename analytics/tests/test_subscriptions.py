"""Unit test for the GraphQL reading subscription generator."""
import asyncio

import pytest

from app.broadcaster import broadcaster
from app.resolvers.subscriptions import Subscription


@pytest.mark.asyncio
async def test_reading_added_streams_matching_reading():
    agen = Subscription().reading_added(device_id="d1", sensor_type="temperature")
    fut = asyncio.ensure_future(agen.__anext__())
    await asyncio.sleep(0.05)  # allow the generator to subscribe

    # Non-matching reading is filtered out
    await broadcaster.publish({"device_id": "other", "sensor_type": "temperature", "value": 9, "unit": "C", "recorded_at": "2026-01-01T00:00:00+00:00"})
    # Matching reading is delivered
    await broadcaster.publish({"device_id": "d1", "sensor_type": "temperature", "value": 23.4, "unit": "C", "recorded_at": "2026-01-01T00:00:00+00:00"})

    reading = await asyncio.wait_for(fut, timeout=2)
    assert reading.value == 23.4
    assert reading.device_id == "d1"
    await agen.aclose()
