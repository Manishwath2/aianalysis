from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import optional_db_session
from app.schemas.matching import (
    CandidateMatchRequest,
    CandidateMatchResponse,
    CandidateRankingRequest,
    CandidateRankingResponse,
    RecruiterSummaryRequest,
    RecruiterSummaryResponse,
)
from app.services.matching_service import (
    CandidateResolutionError,
    MatchingServiceError,
    generate_recruiter_summary,
    rank_candidates_for_job,
    score_candidate_against_job,
)

router = APIRouter()


@router.post("/matches/score", response_model=CandidateMatchResponse)
async def match_candidate(
    payload: CandidateMatchRequest,
    session: AsyncSession | None = Depends(optional_db_session),
) -> CandidateMatchResponse:
    try:
        return await score_candidate_against_job(payload, session=session)
    except CandidateResolutionError as exc:
        detail = str(exc)
        status_code = 404 if detail == "Candidate not found" else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc
    except MatchingServiceError as exc:
        detail = str(exc)
        status_code = 404 if detail == "Job not found" else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.post("/matches/rank", response_model=CandidateRankingResponse)
async def rank_candidates(
    payload: CandidateRankingRequest,
    session: AsyncSession | None = Depends(optional_db_session),
) -> CandidateRankingResponse:
    try:
        return await rank_candidates_for_job(payload, session=session)
    except CandidateResolutionError as exc:
        detail = str(exc)
        status_code = 404 if detail == "Candidate not found" else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc
    except MatchingServiceError as exc:
        detail = str(exc)
        status_code = 404 if detail == "Job not found" else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.post("/matches/recruiter-summary", response_model=RecruiterSummaryResponse)
async def recruiter_summary(
    payload: RecruiterSummaryRequest,
    session: AsyncSession | None = Depends(optional_db_session),
) -> RecruiterSummaryResponse:
    try:
        return await generate_recruiter_summary(payload, session=session)
    except CandidateResolutionError as exc:
        detail = str(exc)
        status_code = 404 if detail == "Candidate not found" else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc
    except MatchingServiceError as exc:
        detail = str(exc)
        status_code = 404 if detail == "Job not found" else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc
