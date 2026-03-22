"""
Test 1 — Ingestion flow
Verifies that a sensor reading posted to the ingestion service
is persisted to TimescaleDB and queryable via GraphQL analytics.
"""
from datetime import datetime, timezone

import httpx
import pytest

from conftest import DEVICE_ID, INGESTION_URL, graphql_query, poll_until

SENSOR_TYPE = "temperature"
TEST_VALUE = 27.42  # unique value unlikely to already exist

READINGS_QUERY = """
query Readings($deviceId: String!, $sensorType: String!, $limit: Int!) {
  readings(deviceId: $deviceId, sensorType: $sensorType, limit: $limit) {
    value
    unit
    recordedAt
  }
}
"""


@pytest.mark.asyncio
async def test_reading_reaches_timescaledb(operator_token):
    """
    POST a reading to the ingestion service and verify it appears
    in TimescaleDB within 15 seconds (via GraphQL analytics query).
    """
    recorded_at = datetime.now(timezone.utc).isoformat()

    # 1. Send reading to ingestion service
    async with httpx.AsyncClient(base_url=INGESTION_URL) as client:
        resp = await client.post(
            "/ingest/reading",
            json={
                "device_id": DEVICE_ID,
                "sensor_type": SENSOR_TYPE,
                "value": TEST_VALUE,
                "unit": "C",
                "recorded_at": recorded_at,
            },
            headers={"Authorization": f"Bearer {operator_token}"},
        )
    assert resp.status_code == 202, f"Expected 202, got {resp.status_code}: {resp.text}"

    # 2. Poll GraphQL until the reading appears in the DB
    def reading_persisted():
        data = graphql_query(
            READINGS_QUERY,
            {"deviceId": DEVICE_ID, "sensorType": SENSOR_TYPE, "limit": 50},
        )
        readings = data.get("data", {}).get("readings", [])
        return any(abs(float(r["value"]) - TEST_VALUE) < 0.01 for r in readings)

    poll_until(reading_persisted, timeout=15)

    # 3. Verify reading fields
    data = graphql_query(
        READINGS_QUERY,
        {"deviceId": DEVICE_ID, "sensorType": SENSOR_TYPE, "limit": 50},
    )
    readings = data["data"]["readings"]
    match = next(r for r in readings if abs(float(r["value"]) - TEST_VALUE) < 0.01)

    assert match["unit"] == "C"
    assert match["recordedAt"] is not None
