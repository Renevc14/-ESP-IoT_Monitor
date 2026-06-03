from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import audit, auth, users

app = FastAPI(
    title="IoT Identity Service",
    description="Autenticación JWT, gestión de usuarios (RBAC) y auditoría (OWASP A07/A09)",
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

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(audit.router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "identity"}
