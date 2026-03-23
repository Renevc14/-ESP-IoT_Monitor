"""
Open-Meteo client for Cochabamba, Bolivia.
Fetches real-time weather data used to anchor sensor emulation.

Source: Open-Meteo API (ECMWF model)
Coordinates: Cochabamba, Bolivia (-17.3895, -66.1568)
"""

import logging
import time

import httpx

LATITUDE = -17.3895
LONGITUDE = -66.1568
TIMEZONE = "America/La_Paz"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds between retries

logger = logging.getLogger(__name__)

_last_known: dict | None = None


def fetch_conditions() -> dict:
    """
    Returns current weather conditions for Cochabamba.
    Fields:
      - temperature_2m      (°C)   — outdoor air temperature at 2m
      - relative_humidity_2m (%)   — outdoor relative humidity at 2m
      - shortwave_radiation  (W/m²) — global solar irradiance at surface
      - cloud_cover          (%)   — total cloud cover
      - is_day               (0/1) — whether it's currently daytime

    Retry policy: up to MAX_RETRIES attempts with RETRY_DELAY seconds between each.
    If all attempts fail and a previous successful response exists, returns that
    (last-known-good). If no previous response exists, raises RuntimeError.
    """
    global _last_known
    last_exc: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = httpx.get(
                OPEN_METEO_URL,
                params={
                    "latitude": LATITUDE,
                    "longitude": LONGITUDE,
                    "current": [
                        "temperature_2m",
                        "relative_humidity_2m",
                        "shortwave_radiation",
                        "cloud_cover",
                        "is_day",
                    ],
                    "timezone": TIMEZONE,
                },
                timeout=10.0,
            )
            resp.raise_for_status()
            current = resp.json()["current"]
            logger.info(
                "Weather fetched — temp=%.1f°C hum=%d%% radiation=%.0fW/m² cloud=%d%% is_day=%s",
                current["temperature_2m"],
                current["relative_humidity_2m"],
                current["shortwave_radiation"],
                current["cloud_cover"],
                bool(current["is_day"]),
            )
            _last_known = current
            return current
        except Exception as exc:
            last_exc = exc
            if attempt < MAX_RETRIES:
                logger.warning(
                    "Open-Meteo attempt %d/%d failed (%s) — retrying in %ds",
                    attempt, MAX_RETRIES, exc, RETRY_DELAY,
                )
                time.sleep(RETRY_DELAY)

    if _last_known is not None:
        logger.warning(
            "Open-Meteo unavailable after %d attempts (%s) — using last known conditions",
            MAX_RETRIES, last_exc,
        )
        return _last_known

    raise RuntimeError(f"Open-Meteo unavailable after {MAX_RETRIES} attempts and no cached data: {last_exc}")
