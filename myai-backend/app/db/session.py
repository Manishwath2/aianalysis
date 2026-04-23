from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings


def _create_engine() -> AsyncEngine:
    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not configured")
    return create_async_engine(settings.database_url, pool_pre_ping=True)


_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = _create_engine()
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _sessionmaker


async def get_db_session() -> AsyncIterator[AsyncSession]:
    # Lazy-init: only used when endpoints requiring DB are called.
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        yield session


async def db_healthcheck() -> bool:
    try:
        sessionmaker = get_sessionmaker()
        async with sessionmaker() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
