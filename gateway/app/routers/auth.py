from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse, UserResponse
from app.services.audit_service import client_ip, log_event
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    rotate_refresh_token,
    save_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, body.email, body.password)
    if not user:
        await log_event(
            "login_failed",
            resource="/auth/login",
            ip=client_ip(request),
            details={"email": body.email},
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token(str(user.id), user.role.value)
    refresh_token = create_refresh_token(str(user.id))
    await save_refresh_token(db, user.id, refresh_token)

    await log_event("login_success", user_id=user.id, resource="/auth/login", ip=client_ip(request))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, request: Request, db: AsyncSession = Depends(get_db)):
    result = await rotate_refresh_token(db, body.refresh_token)
    if not result:
        await log_event("token_refresh_failed", resource="/auth/refresh", ip=client_ip(request))
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
    user, access_token, refresh_token = result
    await log_event("token_refresh", user_id=user.id, resource="/auth/refresh", ip=client_ip(request))
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)
