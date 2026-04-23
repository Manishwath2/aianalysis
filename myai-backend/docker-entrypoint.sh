#!/usr/bin/env sh
set -e

cd /app
export PYTHONPATH="/app:${PYTHONPATH:-}"

if [ "${RUN_MIGRATIONS:-}" = "1" ] && [ -n "${DATABASE_URL:-}" ]; then
  echo "Running migrations..."
  python -m alembic upgrade head
fi

exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
