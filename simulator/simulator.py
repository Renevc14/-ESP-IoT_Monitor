"""
IoT Device Simulator — Cochabamba outdoor sensor stations.

Modes:
  MODE=continuous  (default) — runs indefinitely, fetches real Cochabamba
                               weather from Open-Meteo on every cycle.
  MODE=demo        — scripted 3-phase sequence for live demonstrations:
                     Phase 1: normal readings  (8 cycles)
                     Phase 2: anomaly injection (7 readings)
                     Phase 3: recovery          (8 cycles)

Environment variables:
  GATEWAY_URL       — ingestion service base URL (default: http://localhost:8000)
  INGESTION_URL     — direct ingestion URL (default: http://localhost:8001)
  OPERATOR_EMAIL    — JWT login email
  OPERATOR_PASSWORD — JWT login password
  MODE              — continuous | demo
  INTERVAL          — seconds between cycles in continuous mode (default: 60)
"""

import logging
import os
import time
from datetime import datetime, timezone

import httpx

from sensor_model import ANOMALY_READINGS, DEVICE_SENSORS
from weather import fetch_conditions

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8000")
INGESTION_URL = os.getenv("INGESTION_URL", "http://localhost:8001")
OPERATOR_EMAIL = os.getenv("OPERATOR_EMAIL", "operator@iot.local")
OPERATOR_PASSWORD = os.getenv("OPERATOR_PASSWORD", "Operator1234!")
MODE = os.getenv("MODE", "continuous")
INTERVAL = int(os.getenv("INTERVAL", "60"))


class GatewayClient:
    def __init__(self):
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._client = httpx.Client(timeout=15.0)

    def login(self) -> None:
        resp = self._client.post(
            f"{GATEWAY_URL}/auth/login",
            json={"email": OPERATOR_EMAIL, "password": OPERATOR_PASSWORD},
        )
        resp.raise_for_status()
        data = resp.json()
        self._access_token = data["access_token"]
        self._refresh_token = data["refresh_token"]
        logger.info("Logged in as %s", OPERATOR_EMAIL)

    def _refresh(self) -> None:
        resp = self._client.post(
            f"{GATEWAY_URL}/auth/refresh",
            json={"refresh_token": self._refresh_token},
        )
        resp.raise_for_status()
        data = resp.json()
        self._access_token = data["access_token"]
        self._refresh_token = data["refresh_token"]
        logger.info("Access token refreshed")

    def publish(self, device_id: str, sensor_type: str, value: float, unit: str) -> bool:
        payload = {
            "device_id": device_id,
            "sensor_type": sensor_type,
            "value": value,
            "unit": unit,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
        for attempt in range(2):
            try:
                resp = self._client.post(
                    f"{INGESTION_URL}/ingest/reading",
                    json=payload,
                    headers={"Authorization": f"Bearer {self._access_token}"},
                )
                if resp.status_code == 401 and attempt == 0:
                    self._refresh()
                    continue
                resp.raise_for_status()
                return True
            except httpx.HTTPStatusError as exc:
                logger.error("Publish failed: %s", exc)
                return False
        return False


def emit_cycle(client: GatewayClient, weather: dict, label: str = "") -> int:
    """Emit one reading per sensor across all devices. Returns count published."""
    published = 0
    for device_id, sensors in DEVICE_SENSORS.items():
        for sensor_type, model_fn in sensors:
            value, unit = model_fn(weather)
            ok = client.publish(device_id, sensor_type, value, unit)
            status = "✓" if ok else "✗"
            tag = f"[{label}] " if label else ""
            logger.info(
                "%s%s device=%s...%s  %s=%.3f%s",
                tag, status,
                device_id[:8], device_id[-4:],
                sensor_type, value, unit,
            )
            if ok:
                published += 1
    return published


def run_continuous(client: GatewayClient) -> None:
    logger.info("Mode: CONTINUOUS — interval=%ds — Ctrl+C to stop", INTERVAL)
    total = 0
    while True:
        try:
            weather = fetch_conditions()
        except RuntimeError as exc:
            logger.error("Skipping cycle — %s — retrying in %ds", exc, INTERVAL)
            time.sleep(INTERVAL)
            continue
        published = emit_cycle(client, weather)
        total += published
        logger.info("Cycle complete — %d readings published (total: %d)", published, total)
        time.sleep(INTERVAL)


def run_demo(client: GatewayClient) -> None:
    logger.info("Mode: DEMO — 3 phases: normal → anomaly → recovery")
    weather = fetch_conditions()
    total = 0

    # Phase 1 — normal
    logger.info("── Phase 1: Normal readings (8 cycles) ──")
    for i in range(8):
        total += emit_cycle(client, weather, label="NORMAL")
        time.sleep(2)

    # Phase 2 — anomaly injection
    logger.info("── Phase 2: Anomaly injection ──")
    for device_id, sensor_type, value, unit in ANOMALY_READINGS:
        ok = client.publish(device_id, sensor_type, value, unit)
        status = "✓ ALERT EXPECTED" if ok else "✗"
        logger.warning("[ANOMALY] %s  device=...%s  %s=%.2f%s", status, device_id[-4:], sensor_type, value, unit)
        if ok:
            total += 1
        time.sleep(2)

    # Phase 3 — recovery
    logger.info("── Phase 3: Recovery (8 cycles) ──")
    weather = fetch_conditions()  # re-fetch current conditions
    for i in range(8):
        total += emit_cycle(client, weather, label="RECOVERY")
        time.sleep(2)

    logger.info("Demo complete — %d readings published", total)


def main() -> None:
    logger.info("IoT Simulator starting — gateway=%s ingestion=%s", GATEWAY_URL, INGESTION_URL)
    client = GatewayClient()
    client.login()

    if MODE == "demo":
        run_demo(client)
    else:
        run_continuous(client)


if __name__ == "__main__":
    main()
