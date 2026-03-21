from fastapi import FastAPI

app = FastAPI(
    title="IoT Ingestion Service",
    description="Receives sensor data and publishes to RabbitMQ fanout exchange",
    version="1.0.0",
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ingestion"}
