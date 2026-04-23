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


def repair_alembic_version_table(connection: Connection) -> None:
    """Normalize legacy Alembic metadata before resolving the revision graph.

    Earlier builds used descriptive revision ids. Existing databases may already
    be stamped with one of those values. The active revision graph now uses
    short ids, so trim legacy values to their numeric prefix before Alembic
    loads the migration graph.
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
    connection.execute(
        sa.text(
            """
            UPDATE alembic_version
            SET version_num = LEFT(version_num, 4)
            WHERE version_num LIKE '000_\\_%' ESCAPE '\\'
              AND LEFT(version_num, 4) IN ('0001', '0002', '0003')
            """
        )
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
    repair_alembic_version_table(connection)
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
