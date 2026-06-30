"""Proxy de borde: valida el JWT y reenvía a los servicios de dominio."""
import httpx
from fastapi import APIRouter, HTTPException, Request, Response, status
from jose import JWTError, jwt

from app.config import settings

router = APIRouter()

# Prefijo de ruta -> servicio upstream
ROUTES = [
    ("/auth", settings.identity_url),
    ("/users", settings.identity_url),
    ("/audit-logs", settings.identity_url),
    ("/devices", settings.registry_url),
    ("/sensors", settings.registry_url),
    ("/alert-rules", settings.alerts_url),
    ("/alerts", settings.alerts_url),
]

# Rutas públicas (no requieren token)
PUBLIC = {
    "/auth/login", "/auth/refresh", "/auth/logout",
    "/auth/forgot-password", "/auth/reset-password",
}

_HOP_BY_HOP = {"host", "content-length", "transfer-encoding", "connection", "keep-alive"}


def _upstream_for(path: str) -> str | None:
    for prefix, base in ROUTES:
        if path == prefix or path.startswith(prefix + "/"):
            return base
    return None


def _require_valid_token(request: Request) -> None:
    auth = request.headers.get("authorization", "")
    token = auth[7:] if auth.lower().startswith("bearer ") else ""
    try:
        if jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]).get("type") != "access":
            raise JWTError()
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


@router.api_route("/{full_path:path}", methods=["GET", "POST", "PATCH", "PUT", "DELETE"])
async def proxy(full_path: str, request: Request):
    path = "/" + full_path
    base = _upstream_for(path)
    if base is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    if path not in PUBLIC:
        _require_valid_token(request)

    body = await request.body()
    fwd_headers = {k: v for k, v in request.headers.items() if k.lower() not in _HOP_BY_HOP}
    params = [(k, v) for k, v in request.query_params.multi_items()]

    client: httpx.AsyncClient = request.app.state.http
    try:
        upstream = await client.request(
            request.method, f"{base}{path}",
            params=params, content=body, headers=fwd_headers, cookies=request.cookies,
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Upstream unavailable: {exc}")

    resp_headers = {k: v for k, v in upstream.headers.items() if k.lower() not in _HOP_BY_HOP}
    return Response(content=upstream.content, status_code=upstream.status_code, headers=resp_headers)
