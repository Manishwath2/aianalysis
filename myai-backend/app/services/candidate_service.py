from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models.candidate_profile import CandidateProfileRecord
from app.schemas.candidate import CandidateProfile
from app.utils.memory_store import CANDIDATES


class CandidateNotFoundError(Exception):
    pass


def _remember_candidate(candidate: CandidateProfile) -> CandidateProfile:
    CANDIDATES[str(candidate.candidate_id)] = candidate
    return candidate


def _allow_memory_fallback() -> bool:
    settings = get_settings()
    return not settings.database_url or settings.environment.lower() != "production"


async def list_candidates(session: AsyncSession | None) -> list[CandidateProfile]:
    if session is not None:
        try:
            result = await session.execute(
                select(CandidateProfileRecord).order_by(
                    CandidateProfileRecord.full_name.asc(),
                    CandidateProfileRecord.candidate_id.asc(),
                )
            )
            rows = list(result.scalars().all())
            if rows:
                candidates = [CandidateProfile.model_validate(row.document) for row in rows]
                for candidate in candidates:
                    _remember_candidate(candidate)
                return candidates
            return []
        except Exception:
            if not _allow_memory_fallback():
                raise

    return sorted(CANDIDATES.values(), key=lambda item: (item.personal.full_name.lower(), str(item.candidate_id)))


async def save_candidate(session: AsyncSession | None, candidate: CandidateProfile) -> CandidateProfile:
    payload = candidate.model_dump(mode="json")
    if session is not None:
        try:
            record = await session.get(CandidateProfileRecord, candidate.candidate_id)
            if record is None:
                record = CandidateProfileRecord(
                    candidate_id=candidate.candidate_id,
                    full_name=candidate.personal.full_name,
                    headline=candidate.personal.headline,
                    location=candidate.personal.location,
                    source=(candidate.meta.source if candidate.meta else None),
                    document=payload,
                )
                session.add(record)
            else:
                record.full_name = candidate.personal.full_name
                record.headline = candidate.personal.headline
                record.location = candidate.personal.location
                record.source = candidate.meta.source if candidate.meta else None
                record.document = payload

            await session.commit()
        except Exception:
            await session.rollback()
            if not _allow_memory_fallback():
                raise
            return _remember_candidate(candidate)

    return _remember_candidate(candidate)


async def get_candidate(
    session: AsyncSession | None,
    candidate_id: str,
) -> CandidateProfile:
    if session is not None:
        try:
            record = await session.get(CandidateProfileRecord, candidate_id)
            if record is not None:
                candidate = CandidateProfile.model_validate(record.document)
                return _remember_candidate(candidate)
        except Exception:
            if not _allow_memory_fallback():
                raise

    candidate = CANDIDATES.get(candidate_id)
    if candidate is None:
        raise CandidateNotFoundError("Candidate not found")
    return candidate
