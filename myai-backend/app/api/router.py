from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import ai, auth, candidates, chat, health, jobs, llm, matches, resumes, templates

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/v1", tags=["auth"])
api_router.include_router(llm.router, prefix="/v1", tags=["llm"])
api_router.include_router(chat.router, prefix="/v1", tags=["chat"])
api_router.include_router(ai.router, prefix="/v1", tags=["ai"])
api_router.include_router(candidates.router, prefix="/v1", tags=["candidates"])
api_router.include_router(jobs.router, prefix="/v1", tags=["jobs"])
api_router.include_router(matches.router, prefix="/v1", tags=["matches"])
api_router.include_router(resumes.router, prefix="/v1", tags=["resumes"])
api_router.include_router(templates.router, prefix="/v1", tags=["templates"])

