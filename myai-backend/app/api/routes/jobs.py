from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import optional_db_session
from app.schemas.job import JobDescription
from app.services.job_service import JobResolutionError, list_jobs, resolve_job, store_job

router = APIRouter()


@router.get("/jobs", response_model=list[JobDescription])
async def get_jobs(
    session: AsyncSession | None = Depends(optional_db_session),
) -> list[JobDescription]:
    return await list_jobs(session)


@router.post("/jobs/validate", response_model=JobDescription)
def validate_job(job: JobDescription) -> JobDescription:
    return job


@router.post("/jobs", response_model=JobDescription)
async def create_job(
    job: JobDescription,
    session: AsyncSession | None = Depends(optional_db_session),
) -> JobDescription:
    return await store_job(session, job)


@router.get("/jobs/{job_id}", response_model=JobDescription)
async def get_job(
    job_id: str,
    session: AsyncSession | None = Depends(optional_db_session),
) -> JobDescription:
    try:
        return await resolve_job(session=session, job=None, job_id=job_id)
    except JobResolutionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
