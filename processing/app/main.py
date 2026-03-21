from fastapi import FastAPI

app = FastAPI(
    title="IoT Processing Service",
    description="Consumes RabbitMQ events, persists to TimescaleDB and Redis",
    version="1.0.0",
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "processing"}
