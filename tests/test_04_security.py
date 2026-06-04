"""
Test 4 — Controles de seguridad (autorización consistente)
Verifica que los endpoints sensibles rechazan peticiones sin token y que un
token válido sí concede acceso (OWASP A01 — Broken Access Control).
"""
import httpx
import pytest

from conftest import ALERTS_URL, ANALYTICS_URL, GATEWAY_URL


@pytest.mark.asyncio
async def test_graphql_requires_token():
    resp = httpx.post(
        f"{ANALYTICS_URL}/graphql",
        json={"query": "{ readings(limit: 1) { value } }"},
        timeout=10.0,
    )
    assert resp.status_code == 401, f"GraphQL debería exigir token: {resp.status_code}"


@pytest.mark.asyncio
async def test_export_requires_token():
    resp = httpx.get(f"{ANALYTICS_URL}/export/readings.csv", timeout=10.0)
    assert resp.status_code in (401, 403), f"Export debería exigir token: {resp.status_code}"


@pytest.mark.asyncio
async def test_alerts_list_requires_token():
    resp = httpx.get(f"{ALERTS_URL}/alerts", timeout=10.0)
    assert resp.status_code in (401, 403), f"Listado de alertas debería exigir token: {resp.status_code}"


@pytest.mark.asyncio
async def test_gateway_protected_route_requires_token():
    resp = httpx.get(f"{GATEWAY_URL}/devices", timeout=10.0)
    assert resp.status_code == 401, f"El gateway debería exigir token: {resp.status_code}"


@pytest.mark.asyncio
async def test_gateway_grants_access_with_token(admin_token):
    resp = httpx.get(
        f"{GATEWAY_URL}/devices",
        headers={"Authorization": f"Bearer {admin_token}"},
        timeout=10.0,
    )
    assert resp.status_code == 200, f"Con token válido debería conceder acceso: {resp.text}"
