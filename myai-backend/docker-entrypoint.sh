#!/usr/bin/env sh
set -e

if [ "${RUN_MIGRATIONS:-}" = "1" ] && [ -n "${DATABASE_URL:-}" ]; then
  echo "Running migrations..."
  alembic upgrade head
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
