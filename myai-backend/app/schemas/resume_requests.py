from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.candidate import CandidateProfile
from app.schemas.resume import ResumeDocument, ResumeWarning
from app.schemas.templates import ResumeTemplateDefinition


class ResumeAIOptions(BaseModel):
    enabled: bool = False
    enrichments: list[str] = Field(default_factory=list)
    provider: str | None = None
    model: str | None = None
    apply_if_missing: bool = True
    max_bullets_per_item: int = Field(default=3, ge=1, le=8)


class ResumeGenerateRequest(BaseModel):
    template_id: str = Field(default="classic", min_length=1, max_length=60)
    template_version: str | None = Field(default=None, max_length=40)
    locale: str = Field(default="en-US", max_length=20)

    candidate_id: str | None = None
    candidate: CandidateProfile | None = None


class ResumeGenerateBundleRequest(ResumeGenerateRequest):
    include_candidate: bool = True
    include_template: bool = True
    ai: ResumeAIOptions | None = None


class ResumeProvenance(BaseModel):
    deterministic: bool = True
    ai_used: bool = False
    ai_provider: str | None = None
    ai_model: str | None = None
    ai_enrichments: list[str] = Field(default_factory=list)


class ResumeTemplateDataResponse(BaseModel):
    candidate: CandidateProfile | None = None
    template: ResumeTemplateDefinition | None = None
    resume: ResumeDocument
    warnings: list[ResumeWarning] = Field(default_factory=list)
    provenance: ResumeProvenance = Field(default_factory=ResumeProvenance)

