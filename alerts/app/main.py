import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app import consumer
from app.config import settings
from app.observability import setup_observability
from app.routers.alerts import router
from app.routers.rules import router as rules_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    app.state.session_factory = session_factory

    consume_task = asyncio.create_task(consumer.start_consuming(session_factory))

    yield

    consume_task.cancel()
    try:
        await consume_task
    except asyncio.CancelledError:
        pass

    await consumer.stop_consuming()
    await engine.dispose()


app = FastAPI(
    title="IoT Alerts Service",
    description="Threshold evaluation engine with WebSocket real-time broadcast",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_observability(app, "alerts")

app.include_router(router)
app.include_router(rules_router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "alerts"}
