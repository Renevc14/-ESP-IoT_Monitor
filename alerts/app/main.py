from fastapi import FastAPI

app = FastAPI(
    title="IoT Alerts Service",
    description="Threshold evaluation engine with WebSocket real-time broadcast",
    version="1.0.0",
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "alerts"}
