from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.core.config import get_settings


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(*, user_id: str) -> str:
    settings = get_settings()
    exp = _now() + timedelta(minutes=settings.jwt_access_token_minutes)
    payload = {"sub": user_id, "type": "access", "exp": exp}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def create_refresh_token(*, user_id: str) -> str:
    settings = get_settings()
    exp = _now() + timedelta(days=settings.jwt_refresh_token_days)
    payload = {"sub": user_id, "type": "refresh", "exp": exp}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        if payload.get("type") != "access":
            raise JWTError("Wrong token type")
        return payload
    except JWTError as e:
        raise ValueError("Invalid access token") from e


def decode_refresh_token(token: str) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            raise JWTError("Wrong token type")
        return payload
    except JWTError as e:
        raise ValueError("Invalid refresh token") from e
