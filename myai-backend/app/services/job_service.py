from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models.job_description import JobDescriptionRecord
from app.schemas.job import JobDescription
from app.utils.memory_store import JOBS


class JobResolutionError(Exception):
    pass


def _remember_job(job: JobDescription) -> JobDescription:
    JOBS[str(job.job_id)] = job
    return job


def _allow_memory_fallback() -> bool:
    settings = get_settings()
    return not settings.database_url or settings.environment.lower() != "production"


async def resolve_job(
    *,
    session: AsyncSession | None,
    job: JobDescription | None,
    job_id: str | None,
) -> JobDescription:
    if job is not None:
        return job
    if not job_id:
        raise JobResolutionError("Provide job or job_id")

    if session is not None:
        try:
            record = await session.get(JobDescriptionRecord, job_id)
            if record is not None:
                job = JobDescription.model_validate(record.document)
                return _remember_job(job)
        except Exception:
            if not _allow_memory_fallback():
                raise

    stored = JOBS.get(job_id)
    if stored is None:
        raise JobResolutionError("Job not found")
    return stored


async def store_job(session: AsyncSession | None, job: JobDescription) -> JobDescription:
    payload = job.model_dump(mode="json")
    if session is not None:
        try:
            record = await session.get(JobDescriptionRecord, job.job_id)
            if record is None:
                record = JobDescriptionRecord(
                    job_id=job.job_id,
                    title=job.title,
                    company=job.company,
                    location=job.location,
                    seniority=job.seniority,
                    work_model=job.work_model,
                    document=payload,
                )
                session.add(record)
            else:
                record.title = job.title
                record.company = job.company
                record.location = job.location
                record.seniority = job.seniority
                record.work_model = job.work_model
                record.document = payload
            await session.commit()
        except Exception:
            await session.rollback()
            if not _allow_memory_fallback():
                raise
            return _remember_job(job)

    return _remember_job(job)


async def list_jobs(session: AsyncSession | None) -> list[JobDescription]:
    if session is not None:
        try:
            result = await session.execute(
                select(JobDescriptionRecord).order_by(
                    JobDescriptionRecord.title.asc(),
                    JobDescriptionRecord.job_id.asc(),
                )
            )
            rows = list(result.scalars().all())
            if rows:
                jobs = [JobDescription.model_validate(row.document) for row in rows]
                for job in jobs:
                    _remember_job(job)
                return jobs
            return []
        except Exception:
            if not _allow_memory_fallback():
                raise

    return sorted(JOBS.values(), key=lambda item: (item.title.lower(), str(item.job_id)))
