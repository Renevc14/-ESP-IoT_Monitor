from contextlib import asynccontextmanager
from typing import List, Optional

import asyncio

import httpx
import strawberry
from fastapi import FastAPI, HTTPException, Request, WebSocket, status
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from strawberry.extensions import QueryDepthLimiter
from strawberry.fastapi import GraphQLRouter

from app import consumer
from app.config import settings
from app.routers.export import router as export_router
from app.resolvers.queries import (
    resolve_alert_summary,
    resolve_alerts,
    resolve_bucketed_readings,
    resolve_device_summary,
    resolve_devices,
    resolve_hourly_readings,
    resolve_readings,
)
from app.resolvers.subscriptions import Subscription
from app.types.schema import AlertSummaryType, AlertType, BucketedReadingType, DeviceSummaryType, DeviceType, SensorReadingType


@strawberry.type
class Query:
    readings: List[SensorReadingType] = strawberry.field(
        resolver=resolve_readings,
        description="Latest sensor readings with optional device/sensor filters",
    )
    device_summary: List[DeviceSummaryType] = strawberry.field(
        resolver=resolve_device_summary,
        description="Aggregated statistics for a device over a time window",
    )
    alert_summary: AlertSummaryType = strawberry.field(
        resolver=resolve_alert_summary,
        description="Platform-wide alert counts by severity and status",
    )
    devices: List[DeviceType] = strawberry.field(
        resolver=resolve_devices,
        description="List registered devices with optional active filter",
    )
    alerts: List[AlertType] = strawberry.field(
        resolver=resolve_alerts,
        description="List alerts with optional device and status filters",
    )
    bucketed_readings: List[BucketedReadingType] = strawberry.field(
        resolver=resolve_bucketed_readings,
        description="Time-bucketed aggregate readings (avg/min/max per bucket) for charting",
    )
    hourly_readings: List[BucketedReadingType] = strawberry.field(
        resolver=resolve_hourly_readings,
        description="Hourly trends from the TimescaleDB continuous aggregate (fast historical queries)",
    )


# Límite de profundidad: evita consultas anidadas abusivas (DoS por complejidad).
schema = strawberry.Schema(
    query=Query,
    subscription=Subscription,
    extensions=[QueryDepthLimiter(max_depth=12)],
)


def _valid_access_token(token: str | None) -> bool:
    if not token or not settings.jwt_secret_key:
        return False
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"]).get("type") == "access"
    except JWTError:
        return False


def _bearer_token(authorization: str | None) -> str | None:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:]
    return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    app.state.session_factory = session_factory
    # Cliente HTTP compartido para la composición de API (keep-alive entre peticiones).
    http_client = httpx.AsyncClient(timeout=10)
    app.state.http = http_client

    async def get_context(request: Request = None, websocket: WebSocket = None) -> dict:
        # En WebSocket (suscripciones) exigimos un access token válido por query param.
        if websocket is not None:
            if not _valid_access_token(websocket.query_params.get("token")):
                await websocket.close(code=1008)
                raise RuntimeError("unauthorized websocket")
            return {"session_factory": session_factory, "auth": None, "http": http_client}
        # En HTTP exigimos un access token válido y lo reenviamos a la composición de API.
        auth = request.headers.get("authorization") if request is not None else None
        if not _valid_access_token(_bearer_token(auth)):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
        return {"session_factory": session_factory, "auth": auth, "http": http_client}

    graphql_app = GraphQLRouter(schema, context_getter=get_context)
    app.include_router(graphql_app, prefix="/graphql")

    # Real-time: consume the fanout exchange and feed GraphQL subscriptions
    consume_task = asyncio.create_task(consumer.start_consuming())

    yield

    consume_task.cancel()
    try:
        await consume_task
    except asyncio.CancelledError:
        pass
    await consumer.stop_consuming()
    await http_client.aclose()
    await engine.dispose()


app = FastAPI(
    title="IoT Analytics Service",
    description="GraphQL API (Strawberry) for time-series historical queries",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.allowed_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(export_router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "analytics"}
