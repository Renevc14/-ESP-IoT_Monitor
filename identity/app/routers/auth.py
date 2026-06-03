import uuid

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from jose import JWTError
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse, UserResponse
from app.services.audit_service import client_ip, log_event
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    create_reset_token,
    decode_token,
    hash_password,
    rotate_refresh_token,
    save_refresh_token,
)
from app.services.mailer import send_email

router = APIRouter(prefix="/auth", tags=["Authentication"])

REFRESH_MAX_AGE = settings.refresh_token_expire_days * 24 * 3600


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=REFRESH_MAX_AGE,
        path="/",
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, body.email, body.password)
    if not user:
        await log_event("login_failed", resource="/auth/login", ip=client_ip(request), details={"email": body.email})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token(str(user.id), user.role.value)
    refresh_token = create_refresh_token(str(user.id))
    await save_refresh_token(db, user.id, refresh_token)
    _set_refresh_cookie(response, refresh_token)

    await log_event("login_success", user_id=user.id, resource="/auth/login", ip=client_ip(request))

    return TokenResponse(access_token=access_token, refresh_token=refresh_token, user=UserResponse.model_validate(user))


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    body: RefreshRequest | None = None,
    refresh_token: str | None = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    token = (body.refresh_token if body else None) or refresh_token
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")
    result = await rotate_refresh_token(db, token)
    if not result:
        await log_event("token_refresh_failed", resource="/auth/refresh", ip=client_ip(request))
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
    user, access_token, new_refresh = result
    _set_refresh_cookie(response, new_refresh)
    await log_event("token_refresh", user_id=user.id, resource="/auth/refresh", ip=client_ip(request))
    return TokenResponse(access_token=access_token, refresh_token=new_refresh)


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("refresh_token", path="/")
    return {"status": "ok"}


# ── Password recovery ─────────────────────────────────────────────────────────

class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email, User.is_active == True))
    user = result.scalar_one_or_none()
    if user:
        token = create_reset_token(str(user.id))
        link = f"{settings.frontend_url}/reset-password?token={token}"
        await send_email(
            user.email,
            "Recuperación de contraseña — IoT Monitor",
            f"Se solicitó restablecer tu contraseña.\n\nAbre el siguiente enlace (válido 30 minutos):\n{link}\n\n"
            "Si no fuiste tú, ignora este mensaje.",
        )
        await log_event("password_reset_requested", user_id=user.id, resource="/auth/forgot-password", ip=client_ip(request))
    # No revelar si el email existe
    return {"status": "ok", "message": "Si el email existe, se envió un enlace de recuperación"}


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest, request: Request, db: AsyncSession = Depends(get_db)):
    if len(body.new_password) < 8:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 8 caracteres")
    try:
        payload = decode_token(body.token)
        if payload.get("type") != "reset":
            raise ValueError("wrong type")
        user_id = uuid.UUID(payload["sub"])
    except (JWTError, ValueError, KeyError):
        raise HTTPException(status_code=400, detail="Token inválido o expirado")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="Token inválido o expirado")
    user.password_hash = hash_password(body.new_password)
    await db.flush()
    await log_event("password_reset", user_id=user.id, resource="/auth/reset-password", ip=client_ip(request))
    return {"status": "ok", "message": "Contraseña actualizada"}
