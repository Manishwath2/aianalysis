from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import optional_db_session
from app.schemas.candidate import CandidateProfile
from app.services.candidate_service import CandidateNotFoundError, get_candidate, list_candidates, save_candidate

router = APIRouter()


@router.get("/candidates", response_model=list[CandidateProfile])
async def get_candidates(
    session: AsyncSession | None = Depends(optional_db_session),
) -> list[CandidateProfile]:
    return await list_candidates(session)


@router.post("/candidates/validate", response_model=CandidateProfile)
def validate_candidate(candidate: CandidateProfile) -> CandidateProfile:
    return candidate


@router.post("/candidates", response_model=CandidateProfile)
async def create_candidate(
    candidate: CandidateProfile,
    session: AsyncSession | None = Depends(optional_db_session),
) -> CandidateProfile:
    return await save_candidate(session, candidate)


@router.get("/candidates/{candidate_id}", response_model=CandidateProfile)
async def get_candidate_by_id(
    candidate_id: str,
    session: AsyncSession | None = Depends(optional_db_session),
) -> CandidateProfile:
    try:
        return await get_candidate(session, candidate_id)
    except CandidateNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
