from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import devices

app = FastAPI(
    title="IoT Registry Service",
    description="Catálogo de dispositivos IoT (alta/baja/modificación, tokens autogenerados)",
    version="1.0.0",
    contact={"name": "Rene Vilela", "email": "rene.vilela@ucb.edu.bo"},
)

origins = [o.strip() for o in settings.allowed_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(devices.router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "registry"}
