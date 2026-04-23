from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: str) -> User | None:
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        return None
    result = await session.execute(select(User).where(User.id == uid))
    return result.scalar_one_or_none()


async def create_user(
    session: AsyncSession,
    *,
    email: str,
    password: str,
    full_name: str | None,
) -> User:
    user = User(email=email, full_name=full_name)
    user.set_password(password)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
