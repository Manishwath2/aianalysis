from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models.resume_document import ResumeDocumentRecord
from app.schemas.candidate import CandidateProfile, ExperienceItem, ProjectItem
from app.schemas.resume import ResumeDocument
from app.schemas.resume_requests import (
    ResumeGenerateBundleRequest,
    ResumeGenerateRequest,
    ResumeProvenance,
    ResumeTemplateDataResponse,
)
from app.services.ai_enrichment_service import (
    AIEnrichmentError,
    enhance_experience_bullets,
    enhance_project_bullets,
    enrich_candidate,
    generate_summary,
)
from app.services.candidate_service import CandidateNotFoundError, get_candidate
from app.services.resume_compiler import compile_resume
from app.services.resume_template_engine import compile_resume_bundle
from app.services.template_service import get_template_definition
from app.utils.memory_store import RESUMES


class ResumeServiceError(Exception):
    pass


class CandidateResolutionError(ResumeServiceError):
    pass


class TemplateResolutionError(ResumeServiceError):
    pass


def _remember_resume(resume: ResumeDocument) -> ResumeDocument:
    RESUMES[str(resume.resume_id)] = resume
    return resume


def _allow_memory_fallback() -> bool:
    settings = get_settings()
    return not settings.database_url or settings.environment.lower() != "production"


async def resolve_candidate(
    *,
    session: AsyncSession | None,
    candidate: CandidateProfile | None,
    candidate_id: str | None,
) -> CandidateProfile:
    if candidate is not None:
        return candidate
    if not candidate_id:
        raise CandidateResolutionError("Provide candidate or candidate_id")

    try:
        return await get_candidate(session, candidate_id)
    except CandidateNotFoundError as exc:
        raise CandidateResolutionError(str(exc)) from exc


async def store_resume(
    session: AsyncSession | None,
    resume: ResumeDocument,
) -> ResumeDocument:
    payload = resume.model_dump(mode="json")
    if session is not None:
        try:
            record = await session.get(ResumeDocumentRecord, resume.resume_id)
            if record is None:
                record = ResumeDocumentRecord(
                    resume_id=resume.resume_id,
                    candidate_id=resume.candidate_id,
                    template_id=resume.template_id,
                    template_version=resume.template_version,
                    locale=resume.locale,
                    document=payload,
                    created_at=resume.created_at,
                )
                session.add(record)
            else:
                record.candidate_id = resume.candidate_id
                record.template_id = resume.template_id
                record.template_version = resume.template_version
                record.locale = resume.locale
                record.document = payload
                record.created_at = resume.created_at
            await session.commit()
        except Exception:
            await session.rollback()
            if not _allow_memory_fallback():
                raise
            return _remember_resume(resume)

    return _remember_resume(resume)


async def get_resume(
    session: AsyncSession | None,
    resume_id: str,
) -> ResumeDocument | None:
    if session is not None:
        try:
            record = await session.get(ResumeDocumentRecord, resume_id)
            if record is not None:
                resume = ResumeDocument.model_validate(record.document)
                return _remember_resume(resume)
        except Exception:
            if not _allow_memory_fallback():
                raise
    return RESUMES.get(resume_id)


async def generate_resume_document(
    payload: ResumeGenerateRequest,
    *,
    session: AsyncSession | None,
) -> ResumeDocument:
    candidate = await resolve_candidate(
        session=session,
        candidate=payload.candidate,
        candidate_id=payload.candidate_id,
    )
    resume = compile_resume(
        candidate=candidate,
        template_id=payload.template_id,
        locale=payload.locale,
    )
    return await store_resume(session, resume)


async def generate_resume_template_data(
    payload: ResumeGenerateBundleRequest,
    *,
    session: AsyncSession | None,
) -> ResumeTemplateDataResponse:
    candidate = await resolve_candidate(
        session=session,
        candidate=payload.candidate,
        candidate_id=payload.candidate_id,
    )
    template = await get_template_definition(
        session,
        template_id=payload.template_id,
        template_version=payload.template_version,
    )
    if template is None:
        raise TemplateResolutionError("Template not found")

    provenance = ResumeProvenance(deterministic=True, ai_used=False)
    transformed_candidate = candidate

    if payload.ai and payload.ai.enabled:
        transformed_candidate, ai_meta = await enrich_candidate(candidate, payload.ai)
        provenance = ResumeProvenance(
            deterministic=False,
            ai_used=True,
            ai_provider=ai_meta.get("ai_provider"),
            ai_model=ai_meta.get("ai_model"),
            ai_enrichments=ai_meta.get("ai_enrichments", []),
        )

    resume, warnings = compile_resume_bundle(
        candidate=transformed_candidate,
        template=template,
        locale=payload.locale,
    )
    await store_resume(session, resume)

    return ResumeTemplateDataResponse(
        candidate=transformed_candidate if payload.include_candidate else None,
        template=template if payload.include_template else None,
        resume=resume,
        warnings=warnings,
        provenance=provenance,
    )


async def generate_resume_summary(
    candidate: CandidateProfile,
    *,
    provider: str | None = None,
    model: str | None = None,
) -> tuple[str | None, str, str]:
    return await generate_summary(candidate, provider=provider, model=model)


async def enhance_resume_experience_bullets(
    item: ExperienceItem,
    *,
    max_bullets: int = 3,
    provider: str | None = None,
    model: str | None = None,
) -> tuple[list[str], str, str]:
    return await enhance_experience_bullets(
        item,
        max_bullets=max_bullets,
        provider=provider,
        model=model,
    )


async def enhance_resume_project_bullets(
    item: ProjectItem,
    *,
    max_bullets: int = 3,
    provider: str | None = None,
    model: str | None = None,
) -> tuple[list[str], str, str]:
    return await enhance_project_bullets(
        item,
        max_bullets=max_bullets,
        provider=provider,
        model=model,
    )


__all__ = [
    "AIEnrichmentError",
    "CandidateResolutionError",
    "ResumeServiceError",
    "TemplateResolutionError",
    "enhance_resume_experience_bullets",
    "enhance_resume_project_bullets",
    "generate_resume_document",
    "generate_resume_summary",
    "generate_resume_template_data",
    "get_resume",
    "resolve_candidate",
]
