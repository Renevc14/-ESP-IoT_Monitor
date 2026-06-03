"""Autenticación basada en claims del JWT (sin BD de usuarios)."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import settings

bearer = HTTPBearer()


class Principal:
    def __init__(self, user_id: str | None, role: str | None):
        self.id = user_id
        self.role = role


def get_current_principal(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> Principal:
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret_key, algorithms=["HS256"])
        if payload.get("type") != "access":
            raise JWTError()
        return Principal(payload.get("sub"), payload.get("role"))
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


def require_role(*roles: str):
    async def _check(principal: Principal = Depends(get_current_principal)) -> Principal:
        if principal.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Required role: {list(roles)}")
        return principal
    return _check


require_admin = require_role("admin")
require_operator = require_role("admin", "operator")
