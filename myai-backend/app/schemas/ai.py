from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.candidate import CandidateProfile, ExperienceItem, ProjectItem


class AIProviderOptions(BaseModel):
    provider: str | None = None
    model: str | None = None
    max_bullets_per_item: int = Field(default=3, ge=1, le=8)


class AISummaryRequest(BaseModel):
    candidate: CandidateProfile
    options: AIProviderOptions | None = None


class AISummaryResponse(BaseModel):
    summary: str | None = None
    provider: str | None = None
    model: str | None = None


class AIExperienceBulletsRequest(BaseModel):
    item: ExperienceItem
    options: AIProviderOptions | None = None


class AIProjectBulletsRequest(BaseModel):
    item: ProjectItem
    options: AIProviderOptions | None = None


class AIBulletsResponse(BaseModel):
    bullets: list[str]
    provider: str | None = None
    model: str | None = None
