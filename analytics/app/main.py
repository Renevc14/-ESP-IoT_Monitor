from contextlib import asynccontextmanager
from typing import List, Optional

import strawberry
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from strawberry.fastapi import GraphQLRouter

from app.config import settings
from app.resolvers.queries import (
    resolve_alert_summary,
    resolve_alerts,
    resolve_device_summary,
    resolve_devices,
    resolve_readings,
)
from app.types.schema import AlertSummaryType, AlertType, DeviceSummaryType, DeviceType, SensorReadingType


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


schema = strawberry.Schema(query=Query)


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    app.state.session_factory = session_factory

    async def get_context() -> dict:
        return {"session_factory": session_factory}

    graphql_app = GraphQLRouter(schema, context_getter=get_context)
    app.include_router(graphql_app, prefix="/graphql")

    yield
    await engine.dispose()


app = FastAPI(
    title="IoT Analytics Service",
    description="GraphQL API (Strawberry) for time-series historical queries",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "analytics"}
