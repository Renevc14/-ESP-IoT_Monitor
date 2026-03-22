"""
Physical sensor models for Cochabamba outdoor IoT stations.

Device roles:
  device-001  Estación meteorológica — Zona Central (temperature + humidity)
  device-002  Estación meteorológica — Zona Norte   (temperature + humidity)
  device-003  Monitor panel solar + batería         (energy in kW, signed)

Energy sign convention:
  positive → panel generating (charging battery / exporting)
  negative → battery discharging (night or overcast)
"""

import random

# Solar panel physical parameters
PANEL_AREA_M2 = 10.0      # m² — small/mid residential installation
PANEL_EFFICIENCY = 0.20   # 20% — monocrystalline panel typical efficiency
BATTERY_DRAW_KW = 1.2     # kW consumed from battery at night
BASE_LOAD_KW = 0.15       # kW — inverter standby + monitoring equipment


def _noise(sigma: float) -> float:
    return random.gauss(0, sigma)


def temperature_central(weather: dict) -> tuple[float, str]:
    """
    Zona Central (device-001): direct outdoor air temperature.
    Sensor noise: ±0.3°C (typical RTD/thermistor accuracy).
    """
    value = round(weather["temperature_2m"] + _noise(0.3), 2)
    return value, "C"


def humidity_central(weather: dict) -> tuple[float, str]:
    """
    Zona Central (device-001): outdoor relative humidity.
    Sensor noise: ±1.5% RH (capacitive sensor accuracy).
    Clamped to [0, 100].
    """
    value = round(min(100.0, max(0.0, weather["relative_humidity_2m"] + _noise(1.5))), 2)
    return value, "%"


def temperature_north(weather: dict) -> tuple[float, str]:
    """
    Zona Norte (device-002): slightly warmer microclimate.
    Zona Norte (Quillacollo corridor) averages ~1.5°C warmer than the city center
    due to lower altitude and less urban tree cover.
    """
    value = round(weather["temperature_2m"] + 1.5 + _noise(0.4), 2)
    return value, "C"


def humidity_north(weather: dict) -> tuple[float, str]:
    """
    Zona Norte (device-002): slightly drier than city centre.
    """
    value = round(min(100.0, max(0.0, weather["relative_humidity_2m"] - 5 + _noise(2.0))), 2)
    return value, "%"


def solar_power(weather: dict) -> tuple[float, str]:
    """
    Panel solar + batería (device-003).

    During the day: power = (irradiance × area × efficiency) / 1000 - base_load
    At night:       power = -battery_draw  (discharging)

    Irradiance source: Open-Meteo shortwave_radiation (W/m²), ECMWF model.
    Result is signed kW rounded to 3 decimal places.
    Noise: ±0.04 kW (inverter measurement accuracy ~2%).
    """
    irradiance = weather["shortwave_radiation"]
    if weather["is_day"] and irradiance > 10:
        gross_kw = (irradiance * PANEL_AREA_M2 * PANEL_EFFICIENCY) / 1000
        net_kw = gross_kw - BASE_LOAD_KW + _noise(0.04)
    else:
        # Night: battery discharging
        net_kw = -BATTERY_DRAW_KW + _noise(0.04)

    return round(net_kw, 3), "kW"


# Readings emitted per device per cycle
DEVICE_SENSORS = {
    "d0000000-0000-0000-0000-000000000001": [
        ("temperature", temperature_central),
        ("humidity", humidity_central),
    ],
    "d0000000-0000-0000-0000-000000000002": [
        ("temperature", temperature_north),
        ("humidity", humidity_north),
    ],
    "d0000000-0000-0000-0000-000000000003": [
        ("energy", solar_power),
    ],
}

# Anomaly overrides for demo mode
ANOMALY_READINGS = [
    # Heat wave / sensor in direct sun — triggers WARNING (>35) + CRITICAL (>40)
    ("d0000000-0000-0000-0000-000000000001", "temperature", 42.3, "C"),
    ("d0000000-0000-0000-0000-000000000001", "temperature", 39.8, "C"),
    ("d0000000-0000-0000-0000-000000000001", "temperature", 41.1, "C"),
    # Heavy afternoon rain — triggers humidity CRITICAL (>90)
    ("d0000000-0000-0000-0000-000000000001", "humidity", 93.5, "%"),
    ("d0000000-0000-0000-0000-000000000001", "humidity", 91.2, "%"),
    # Inverter fault / panel shading — CRITICAL energy threshold
    ("d0000000-0000-0000-0000-000000000003", "energy", -2.8, "kW"),
    ("d0000000-0000-0000-0000-000000000003", "energy", -3.1, "kW"),
]
