from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_settings
from app.db.session import db_healthcheck
from app.providers.llm.registry import registry

router = APIRouter(tags=["health"])


@router.get("/healthz")
def healthz() -> dict:
    active_provider = registry.get(None).provider_name
    return {"ok": True, "llm_provider": active_provider}


@router.get("/readyz")
async def readyz() -> dict:
    settings = get_settings()
    active_provider = registry.get(None)
    checks: dict[str, str] = {
        "llm": "ok" if active_provider.is_configured() or active_provider.provider_name == "demo" else "down"
    }

    if not settings.database_url:
        checks["db"] = "not-configured"
        return {"ok": True, "checks": checks}

    ok = await db_healthcheck()
    checks["db"] = "ok" if ok else "down"
    return {"ok": ok, "checks": checks}

