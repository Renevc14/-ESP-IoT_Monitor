"""
Test 3 — GraphQL historical data
Seeds multiple readings and verifies that the analytics service
returns correct historical data and aggregate statistics.
"""
from datetime import datetime, timezone

import httpx
import pytest

from conftest import DEVICE_ID, INGESTION_URL, graphql_query, poll_until

SENSOR_TYPE = "humidity"
READINGS_TO_SEND = 10
BASE_VALUE = 55.0  # Normal humidity — will not trigger alerts

READINGS_QUERY = """
query History($deviceId: String!, $sensorType: String!, $limit: Int!) {
  readings(deviceId: $deviceId, sensorType: $sensorType, limit: $limit) {
    value
    unit
    recordedAt
  }
}
"""

SUMMARY_QUERY = """
query Summary($deviceId: String!, $hours: Int!) {
  deviceSummary(deviceId: $deviceId, hours: $hours) {
    deviceId
    sensorType
    readingCount
    minValue
    maxValue
    avgValue
  }
}
"""


@pytest.mark.asyncio
async def test_graphql_returns_history_and_statistics(operator_token):
    """
    1. Insert READINGS_TO_SEND humidity readings via ingestion service.
    2. Poll GraphQL readings query until all readings appear.
    3. Assert count, values, and units are correct.
    4. Query deviceSummary and assert statistical aggregates are populated.
    """
    sent_values = [round(BASE_VALUE + i * 0.5, 1) for i in range(READINGS_TO_SEND)]

    # 1. Send readings
    async with httpx.AsyncClient(base_url=INGESTION_URL) as client:
        for value in sent_values:
            resp = await client.post(
                "/ingest/reading",
                json={
                    "device_id": DEVICE_ID,
                    "sensor_type": SENSOR_TYPE,
                    "value": value,
                    "unit": "%",
                    "recorded_at": datetime.now(timezone.utc).isoformat(),
                },
                headers={"Authorization": f"Bearer {operator_token}"},
            )
            assert resp.status_code == 202

    # 2. Poll until all readings are queryable
    def all_readings_present():
        data = graphql_query(
            READINGS_QUERY,
            {"deviceId": DEVICE_ID, "sensorType": SENSOR_TYPE, "limit": 100},
        )
        assert "errors" not in data or not data["errors"], f"GraphQL error: {data}"
        readings = data["data"]["readings"]
        received_values = {round(float(r["value"]), 1) for r in readings}
        return all(v in received_values for v in sent_values)

    poll_until(all_readings_present, timeout=20)

    # 3. Verify readings response
    data = graphql_query(
        READINGS_QUERY,
        {"deviceId": DEVICE_ID, "sensorType": SENSOR_TYPE, "limit": 100},
    )
    assert not data.get("errors"), f"GraphQL errors: {data.get('errors')}"
    readings = data["data"]["readings"]
    assert len(readings) >= READINGS_TO_SEND

    for r in readings:
        assert r["unit"] == "%"
        assert r["recordedAt"] is not None

    # 4. Verify deviceSummary aggregates
    summary_data = graphql_query(
        SUMMARY_QUERY,
        {"deviceId": DEVICE_ID, "hours": 1},
    )
    assert not summary_data.get("errors"), f"GraphQL errors: {summary_data.get('errors')}"

    summaries = summary_data["data"]["deviceSummary"]
    humidity_summary = next(
        (s for s in summaries if s["sensorType"] == SENSOR_TYPE), None
    )
    assert humidity_summary is not None, "No humidity summary found"
    assert humidity_summary["readingCount"] >= READINGS_TO_SEND
    assert humidity_summary["minValue"] is not None
    assert humidity_summary["maxValue"] is not None
    assert humidity_summary["avgValue"] is not None
    assert float(humidity_summary["minValue"]) <= float(humidity_summary["maxValue"])
