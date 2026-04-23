from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
import sqlalchemy as sa
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import get_settings
from app.db.base import Base
from app.db import models  # noqa: F401


config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def get_url() -> str:
    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not configured")
    return settings.database_url


target_metadata = Base.metadata


def widen_alembic_version_column(connection: Connection) -> None:
    """Allow descriptive Alembic revision ids on existing Postgres databases.

    Some managed/deployed databases may have an alembic_version.version_num
    column created as VARCHAR(32). Our descriptive revision ids are longer than
    that, so the version update can fail after a migration succeeds. Widen this
    metadata column before Alembic writes the next revision.
    """
    if connection.dialect.name != "postgresql":
        return

    exists = connection.execute(
        sa.text("SELECT to_regclass('public.alembic_version') IS NOT NULL")
    ).scalar()
    if not exists:
        return

    connection.execute(
        sa.text("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(128)")
    )


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    widen_alembic_version_column(connection)
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
