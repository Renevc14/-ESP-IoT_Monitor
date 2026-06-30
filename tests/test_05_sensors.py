"""
Test 5 — Catálogo de sensores
Verifica la entidad 'sensors' del modelo de datos: el gateway expone el catálogo
de sensores por dispositivo (registry) y exige autenticación.
"""
import httpx
import pytest

from conftest import GATEWAY_URL


@pytest.mark.asyncio
async def test_sensors_catalog(admin_token):
    resp = httpx.get(
        f"{GATEWAY_URL}/sensors",
        headers={"Authorization": f"Bearer {admin_token}"},
        timeout=10.0,
    )
    assert resp.status_code == 200, f"Esperado 200: {resp.text}"
    sensors = resp.json()
    assert len(sensors) >= 7, f"Se esperaban al menos 7 sensores sembrados, hay {len(sensors)}"
    types = {s["sensor_type"] for s in sensors}
    assert {"temperature", "humidity", "energy"} <= types


@pytest.mark.asyncio
async def test_sensors_requires_token():
    resp = httpx.get(f"{GATEWAY_URL}/sensors", timeout=10.0)
    assert resp.status_code == 401
