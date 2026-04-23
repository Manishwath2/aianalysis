from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db_session
from app.schemas.auth import AuthUser
from app.services.auth_service import decode_access_token
from app.services.user_service import get_user_by_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login")


async def db_session() -> AsyncIterator[AsyncSession]:
    settings = get_settings()
    if not settings.database_url:
        raise HTTPException(status_code=503, detail="Database is not configured")
    async for session in get_db_session():
        yield session


async def optional_db_session() -> AsyncIterator[AsyncSession | None]:
    settings = get_settings()
    if not settings.database_url:
        yield None
        return
    async for session in get_db_session():
        yield session


async def current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(db_session),
) -> AuthUser:
    try:
        payload = decode_access_token(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await get_user_by_id(session, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return AuthUser.model_validate(user)
