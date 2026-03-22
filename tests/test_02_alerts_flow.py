"""
Test 2 — Alert engine flow
Sends an over-threshold reading and verifies that an alert is generated,
then acknowledges it and confirms the status change.
"""
from datetime import datetime, timezone

import httpx
import pytest

from conftest import ALERTS_URL, DEVICE_ID, GATEWAY_URL, INGESTION_URL, poll_until

SENSOR_TYPE = "temperature"
# Seed has: temperature > 40.0 = critical for DEVICE_ID
OVER_THRESHOLD_VALUE = 45.5


@pytest.mark.asyncio
async def test_alert_generated_and_acknowledged(admin_token, operator_token):
    """
    1. Send a temperature reading above the critical threshold (>40°C).
    2. Poll GET /alerts until an alert with the triggered value appears.
    3. Assert severity=critical and status=active.
    4. PATCH /alerts/{id}/acknowledge and assert status=acknowledged.
    """
    recorded_at = datetime.now(timezone.utc).isoformat()

    # 1. Send over-threshold reading
    async with httpx.AsyncClient(base_url=INGESTION_URL) as client:
        resp = await client.post(
            "/ingest/reading",
            json={
                "device_id": DEVICE_ID,
                "sensor_type": SENSOR_TYPE,
                "value": OVER_THRESHOLD_VALUE,
                "unit": "C",
                "recorded_at": recorded_at,
            },
            headers={"Authorization": f"Bearer {operator_token}"},
        )
    assert resp.status_code == 202, f"Expected 202, got {resp.status_code}: {resp.text}"

    # 2. Poll GET /alerts until our alert appears
    def alert_generated():
        resp = httpx.get(
            f"{GATEWAY_URL}/alerts",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=10.0,
        )
        resp.raise_for_status()
        alerts = resp.json()
        return next(
            (
                a for a in alerts
                if a["device_id"] == DEVICE_ID
                and abs(float(a["triggered_value"]) - OVER_THRESHOLD_VALUE) < 0.1
                and a["status"] == "active"
            ),
            None,
        )

    alert = poll_until(alert_generated, timeout=15)

    # 3. Assert severity and status
    assert alert["severity"] == "critical", f"Expected critical, got {alert['severity']}"
    assert alert["status"] == "active"

    # 4. Acknowledge and verify
    async with httpx.AsyncClient(base_url=GATEWAY_URL) as client:
        ack_resp = await client.patch(
            f"/alerts/{alert['id']}/acknowledge",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
    assert ack_resp.status_code == 200, f"Acknowledge failed: {ack_resp.text}"
    assert ack_resp.json()["status"] == "acknowledged"
