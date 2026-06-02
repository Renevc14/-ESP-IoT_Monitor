from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis

from app.config import settings
from app.middleware.rate_limiter import rate_limit_middleware
from app.middleware.security_headers import security_headers_middleware
from app.routers import alert_rules, alerts_proxy, auth, devices, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: connect Redis
    app.state.redis = Redis.from_url(settings.redis_url, decode_responses=True)
    yield
    # Shutdown: close Redis
    await app.state.redis.aclose()


tags_metadata = [
    {"name": "Authentication", "description": "Login y refresh de JWT (access 15 min, refresh 7 días con rotación)."},
    {"name": "Users", "description": "Gestión de usuarios y roles RBAC admin/operator/viewer (solo admin)."},
    {"name": "Devices", "description": "Alta, baja y modificación de dispositivos IoT (solo admin)."},
    {"name": "Alert Rules", "description": "Configuración de umbrales de alerta por dispositivo y sensor."},
    {"name": "Alerts", "description": "Consulta, reconocimiento y resolución de alertas (proxy al servicio de alertas)."},
    {"name": "Health", "description": "Estado operativo del servicio."},
]

app = FastAPI(
    title="IoT API Gateway",
    description=(
        "Punto de entrada único de la plataforma de monitoreo IoT. "
        "Centraliza autenticación JWT, autorización RBAC, rate limiting, "
        "headers de seguridad (OWASP A05) y auditoría de accesos (OWASP A09)."
    ),
    version="1.0.0",
    openapi_tags=tags_metadata,
    contact={"name": "Rene Vilela", "email": "rene.vilela@ucb.edu.bo"},
    lifespan=lifespan,
)

# CORS
origins = [o.strip() for o in settings.allowed_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers + rate limiting middleware
app.middleware("http")(security_headers_middleware)
app.middleware("http")(rate_limit_middleware)

# Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(devices.router)
app.include_router(alert_rules.router)
app.include_router(alerts_proxy.router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "gateway"}
