from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.candidate import CandidateProfile
from app.schemas.job import JobDescription


MatchBand = Literal["strong", "good", "moderate", "weak"]


class RecruiterAIOptions(BaseModel):
    enabled: bool = True
    provider: str | None = None
    model: str | None = None


class MatchScoreBreakdown(BaseModel):
    skill_score: float = Field(ge=0, le=100)
    keyword_score: float = Field(ge=0, le=100)
    experience_score: float = Field(ge=0, le=100)
    seniority_score: float = Field(ge=0, le=100)


class CandidateMatchResult(BaseModel):
    candidate_id: str
    candidate_name: str
    score: float = Field(ge=0, le=100)
    band: MatchBand
    breakdown: MatchScoreBreakdown
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    keyword_hits: list[str] = Field(default_factory=list)
    experience_years: float = 0
    highlights: list[str] = Field(default_factory=list)
    recruiter_summary: str | None = None


class CandidateMatchRequest(BaseModel):
    candidate_id: str | None = None
    candidate: CandidateProfile | None = None
    job_id: str | None = None
    job: JobDescription | None = None
    summary_options: RecruiterAIOptions | None = None


class CandidateMatchResponse(BaseModel):
    job_id: str
    result: CandidateMatchResult


class CandidateRankingRequest(BaseModel):
    job_id: str | None = None
    job: JobDescription | None = None
    candidate_ids: list[str] = Field(default_factory=list)
    candidates: list[CandidateProfile] = Field(default_factory=list)
    top_k: int = Field(default=10, ge=1, le=100)
    include_recruiter_summary: bool = True
    summary_options: RecruiterAIOptions | None = None


class CandidateRankingResponse(BaseModel):
    job_id: str
    job_title: str
    total_candidates: int = 0
    ranked_candidates: list[CandidateMatchResult] = Field(default_factory=list)


class RecruiterSummaryRequest(BaseModel):
    candidate_id: str | None = None
    candidate: CandidateProfile | None = None
    job_id: str | None = None
    job: JobDescription | None = None
    match_result: CandidateMatchResult | None = None
    options: RecruiterAIOptions | None = None


class RecruiterSummaryResponse(BaseModel):
    summary: str
    provider: str | None = None
    model: str | None = None
