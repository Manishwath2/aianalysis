from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.ai import (
    AIBulletsResponse,
    AIExperienceBulletsRequest,
    AIProjectBulletsRequest,
    AISummaryRequest,
    AISummaryResponse,
)
from app.services.resume_service import (
    AIEnrichmentError,
    enhance_resume_experience_bullets,
    enhance_resume_project_bullets,
    generate_resume_summary,
)

router = APIRouter()


@router.post("/ai/summary", response_model=AISummaryResponse)
async def ai_summary(payload: AISummaryRequest) -> AISummaryResponse:
    opts = payload.options
    try:
        summary, provider, model = await generate_resume_summary(
            payload.candidate,
            provider=opts.provider if opts else None,
            model=opts.model if opts else None,
        )
    except AIEnrichmentError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return AISummaryResponse(summary=summary, provider=provider, model=model)


@router.post("/ai/enhance/experience", response_model=AIBulletsResponse)
async def ai_enhance_experience(payload: AIExperienceBulletsRequest) -> AIBulletsResponse:
    opts = payload.options
    try:
        bullets, provider, model = await enhance_resume_experience_bullets(
            payload.item,
            max_bullets=opts.max_bullets_per_item if opts else 3,
            provider=opts.provider if opts else None,
            model=opts.model if opts else None,
        )
    except AIEnrichmentError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return AIBulletsResponse(bullets=bullets, provider=provider, model=model)


@router.post("/ai/enhance/projects", response_model=AIBulletsResponse)
async def ai_enhance_projects(payload: AIProjectBulletsRequest) -> AIBulletsResponse:
    opts = payload.options
    try:
        bullets, provider, model = await enhance_resume_project_bullets(
            payload.item,
            max_bullets=opts.max_bullets_per_item if opts else 3,
            provider=opts.provider if opts else None,
            model=opts.model if opts else None,
        )
    except AIEnrichmentError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return AIBulletsResponse(bullets=bullets, provider=provider, model=model)
