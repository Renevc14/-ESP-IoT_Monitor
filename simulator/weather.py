"""
Open-Meteo client for Cochabamba, Bolivia.
Fetches real-time weather data used to anchor sensor emulation.

Source: Open-Meteo API (ECMWF model)
Coordinates: Cochabamba, Bolivia (-17.3895, -66.1568)
"""

import logging

import httpx

LATITUDE = -17.3895
LONGITUDE = -66.1568
TIMEZONE = "America/La_Paz"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

logger = logging.getLogger(__name__)


def fetch_conditions() -> dict:
    """
    Returns current weather conditions for Cochabamba.
    Fields:
      - temperature_2m      (°C)   — outdoor air temperature at 2m
      - relative_humidity_2m (%)   — outdoor relative humidity at 2m
      - shortwave_radiation  (W/m²) — global solar irradiance at surface
      - cloud_cover          (%)   — total cloud cover
      - is_day               (0/1) — whether it's currently daytime
    """
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
        return current
    except Exception as exc:
        logger.warning("Open-Meteo unavailable (%s) — using fallback values", exc)
        # Fallback: typical Cochabamba midday in March
        return {
            "temperature_2m": 22.0,
            "relative_humidity_2m": 55,
            "shortwave_radiation": 600.0,
            "cloud_cover": 30,
            "is_day": 1,
        }
