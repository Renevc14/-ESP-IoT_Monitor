from fastapi import FastAPI

app = FastAPI(
    title="IoT Analytics Service",
    description="GraphQL API (Strawberry) for time-series historical queries",
    version="1.0.0",
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "analytics"}
