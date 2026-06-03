"""Prueba de carga del servicio de ingesta (RNF-01: >= 1000 eventos/segundo).

Uso:
    pip install httpx
    python tests/load/load_test.py
Variables de entorno: GATEWAY_URL, INGESTION_URL, OPERATOR_EMAIL, OPERATOR_PASSWORD,
                      TOTAL (default 3000), CONCURRENCY (default 100), DEVICE_ID.
"""
import asyncio
import os
import random
import time

import httpx

GATEWAY = os.getenv("GATEWAY_URL", "http://localhost:8000")
INGESTION = os.getenv("INGESTION_URL", "http://localhost:8001")
EMAIL = os.getenv("OPERATOR_EMAIL", "operator@iot.local")
PASSWORD = os.getenv("OPERATOR_PASSWORD", "Operator1234!")
TOTAL = int(os.getenv("TOTAL", "3000"))
CONCURRENCY = int(os.getenv("CONCURRENCY", "100"))
DEVICE_ID = os.getenv("DEVICE_ID", "d0000000-0000-0000-0000-000000000001")


async def main() -> int:
    limits = httpx.Limits(max_connections=CONCURRENCY, max_keepalive_connections=CONCURRENCY)
    async with httpx.AsyncClient(timeout=30, limits=limits) as client:
        resp = await client.post(f"{GATEWAY}/auth/login", json={"email": EMAIL, "password": PASSWORD})
        resp.raise_for_status()
        headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}

        sem = asyncio.Semaphore(CONCURRENCY)
        counters = {"ok": 0, "fail": 0}

        async def one() -> None:
            async with sem:
                try:
                    r = await client.post(
                        f"{INGESTION}/ingest/reading",
                        headers=headers,
                        json={
                            "device_id": DEVICE_ID,
                            "sensor_type": "temperature",
                            "value": round(random.uniform(15, 45), 2),
                            "unit": "C",
                        },
                    )
                    counters["ok" if r.status_code == 202 else "fail"] += 1
                except Exception:
                    counters["fail"] += 1

        start = time.perf_counter()
        await asyncio.gather(*[one() for _ in range(TOTAL)])
        elapsed = time.perf_counter() - start
        throughput = counters["ok"] / elapsed if elapsed else 0

        print(f"Total={TOTAL}  OK={counters['ok']}  Fail={counters['fail']}  "
              f"Elapsed={elapsed:.2f}s  Throughput={throughput:.0f} req/s  "
              f"(objetivo RNF-01: >= 1000 req/s)")
        return 0 if counters["fail"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
