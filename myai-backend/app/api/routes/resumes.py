from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import optional_db_session
from app.schemas.resume import ResumeDocument
from app.schemas.resume_requests import (
    ResumeGenerateBundleRequest,
    ResumeGenerateRequest,
    ResumeTemplateDataResponse,
)
from app.services.resume_service import (
    AIEnrichmentError,
    CandidateResolutionError,
    TemplateResolutionError,
    generate_resume_document,
    generate_resume_template_data,
    get_resume,
)

router = APIRouter()


@router.post("/resumes/generate", response_model=ResumeDocument)
async def generate_resume(
    payload: ResumeGenerateRequest,
    session: AsyncSession | None = Depends(optional_db_session),
) -> ResumeDocument:
    try:
        return await generate_resume_document(payload, session=session)
    except CandidateResolutionError as exc:
        detail = str(exc)
        status_code = 404 if detail == "Candidate not found" else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.post("/resumes/generate-bundle", response_model=ResumeTemplateDataResponse)
async def generate_resume_bundle(
    payload: ResumeGenerateBundleRequest,
    session: AsyncSession | None = Depends(optional_db_session),
) -> ResumeTemplateDataResponse:
    try:
        return await generate_resume_template_data(payload, session=session)
    except CandidateResolutionError as exc:
        detail = str(exc)
        status_code = 404 if detail == "Candidate not found" else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc
    except TemplateResolutionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AIEnrichmentError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/resumes/template-data", response_model=ResumeTemplateDataResponse)
async def generate_template_data(
    payload: ResumeGenerateBundleRequest,
    session: AsyncSession | None = Depends(optional_db_session),
) -> ResumeTemplateDataResponse:
    try:
        return await generate_resume_template_data(payload, session=session)
    except CandidateResolutionError as exc:
        detail = str(exc)
        status_code = 404 if detail == "Candidate not found" else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc
    except TemplateResolutionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AIEnrichmentError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/resumes/{resume_id}", response_model=ResumeDocument)
async def get_resume_by_id(
    resume_id: str,
    session: AsyncSession | None = Depends(optional_db_session),
) -> ResumeDocument:
    resume = await get_resume(session, resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume
