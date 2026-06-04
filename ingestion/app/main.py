from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import publisher
from app.observability import setup_observability
from app.routers import ingest


@asynccontextmanager
async def lifespan(app: FastAPI):
    await publisher.connect()
    yield
    await publisher.disconnect()


app = FastAPI(
    title="IoT Ingestion Service",
    description="Receives sensor data and publishes to RabbitMQ fanout exchange",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

setup_observability(app, "ingestion")

app.include_router(ingest.router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "ingestion"}
