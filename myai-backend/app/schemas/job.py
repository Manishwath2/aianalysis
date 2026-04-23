from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


JobSchemaVersion = Literal["job_description.v1"]
EmploymentType = Literal["full_time", "part_time", "contract", "internship", "freelance"]
WorkModel = Literal["remote", "hybrid", "onsite"]
SeniorityLevel = Literal["intern", "junior", "mid", "senior", "lead", "manager"]


class JobDescription(BaseModel):
    schema_version: JobSchemaVersion = "job_description.v1"
    job_id: UUID
    title: str = Field(min_length=1, max_length=140)
    company: str | None = Field(default=None, max_length=140)
    location: str | None = Field(default=None, max_length=120)
    summary: str | None = Field(default=None, max_length=4000)
    responsibilities: list[str] = Field(default_factory=list)
    must_have_skills: list[str] = Field(default_factory=list)
    nice_to_have_skills: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    minimum_years_experience: float | None = Field(default=None, ge=0, le=50)
    employment_type: EmploymentType | None = None
    work_model: WorkModel | None = None
    seniority: SeniorityLevel | None = None
    education_preferences: list[str] = Field(default_factory=list)


class JobCreateRequest(JobDescription):
    pass
