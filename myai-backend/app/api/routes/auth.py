from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user, db_session
from app.schemas.auth import (
    AuthLoginRequest,
    AuthLoginResponse,
    AuthRefreshRequest,
    AuthRegisterRequest,
    AuthRegisterResponse,
    AuthUser,
)
from app.services.auth_service import create_access_token, create_refresh_token, decode_refresh_token
from app.services.user_service import create_user, get_user_by_email

router = APIRouter(prefix="/auth")


@router.post("/register", response_model=AuthRegisterResponse)
async def register(payload: AuthRegisterRequest, session: AsyncSession = Depends(db_session)):
    existing = await get_user_by_email(session, payload.email)
    if existing is not None:
        raise HTTPException(status_code=409, detail="Email already registered")
    user = await create_user(session, email=payload.email, password=payload.password, full_name=payload.full_name)
    return AuthRegisterResponse(user=AuthUser.model_validate(user))


@router.post("/login", response_model=AuthLoginResponse)
async def login(payload: AuthLoginRequest, session: AsyncSession = Depends(db_session)):
    user = await get_user_by_email(session, payload.email)
    if user is None or not user.verify_password(payload.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User is inactive")

    access = create_access_token(user_id=str(user.id))
    refresh = create_refresh_token(user_id=str(user.id))
    return AuthLoginResponse(
        access_token=access,
        refresh_token=refresh,
        token_type="bearer",
        user=AuthUser.model_validate(user),
    )


@router.post("/refresh", response_model=AuthLoginResponse)
async def refresh(payload: AuthRefreshRequest, session: AsyncSession = Depends(db_session)):
    try:
        claims = decode_refresh_token(payload.refresh_token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user = await get_user_by_email(session, claims.get("email")) if claims.get("email") else None
    # If email wasn't included, just trust sub and fetch by id.
    if user is None:
        from app.services.user_service import get_user_by_id

        user = await get_user_by_id(session, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    access = create_access_token(user_id=str(user.id))
    refresh = create_refresh_token(user_id=str(user.id))
    return AuthLoginResponse(
        access_token=access,
        refresh_token=refresh,
        token_type="bearer",
        user=AuthUser.model_validate(user),
    )


@router.get("/me", response_model=AuthUser)
async def me(user: AuthUser = Depends(current_user)):
    return user
