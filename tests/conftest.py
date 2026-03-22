"""
Shared fixtures for integration tests.
All tests run against the live Docker Compose stack on localhost.
"""
import asyncio
import time

import httpx
import pytest
import pytest_asyncio

GATEWAY_URL = "http://localhost:8000"
INGESTION_URL = "http://localhost:8001"
ALERTS_URL = "http://localhost:8003"
ANALYTICS_URL = "http://localhost:8004"

DEVICE_ID = "d0000000-0000-0000-0000-000000000001"  # Server Room Sensor


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def admin_token():
    async with httpx.AsyncClient(base_url=GATEWAY_URL) as client:
        resp = await client.post(
            "/auth/login",
            json={"email": "admin@iot.local", "password": "Admin1234!"},
        )
        resp.raise_for_status()
        return resp.json()["access_token"]


@pytest_asyncio.fixture(scope="session")
async def operator_token():
    async with httpx.AsyncClient(base_url=GATEWAY_URL) as client:
        resp = await client.post(
            "/auth/login",
            json={"email": "operator@iot.local", "password": "Operator1234!"},
        )
        resp.raise_for_status()
        return resp.json()["access_token"]


def graphql_query(query: str, variables: dict | None = None) -> dict:
    """Synchronous GraphQL helper (used inside poll loops)."""
    payload: dict = {"query": query}
    if variables:
        payload["variables"] = variables
    resp = httpx.post(f"{ANALYTICS_URL}/graphql", json=payload, timeout=10.0)
    resp.raise_for_status()
    return resp.json()


def poll_until(condition_fn, timeout: int = 15, interval: float = 1.0):
    """
    Calls condition_fn() every `interval` seconds until it returns a truthy
    value or `timeout` seconds elapse.  Returns the truthy value or raises.
    """
    deadline = time.time() + timeout
    last_exc = None
    while time.time() < deadline:
        try:
            result = condition_fn()
            if result:
                return result
        except Exception as exc:
            last_exc = exc
        time.sleep(interval)
    raise TimeoutError(
        f"Condition not met within {timeout}s. Last exception: {last_exc}"
    )
