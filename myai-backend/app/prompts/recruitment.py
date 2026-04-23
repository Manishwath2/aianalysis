from __future__ import annotations

from app.schemas.candidate import CandidateProfile
from app.schemas.job import JobDescription
from app.schemas.matching import CandidateMatchResult


def build_recruiter_summary_prompt(
    candidate: CandidateProfile,
    job: JobDescription,
    match_result: CandidateMatchResult,
) -> str:
    return (
        "Write a recruiter-ready candidate assessment in 4 short sentences.\n"
        "Rules:\n"
        "- Stay grounded in the provided candidate and job evidence only.\n"
        "- State overall fit, strongest must-have alignment, experience relevance, and one realistic risk or interview check.\n"
        "- Do not mention unavailable evidence as fact.\n"
        "- Do not use generic filler like 'excellent candidate' without support.\n\n"
        "Evidence:\n"
        f"Candidate name: {candidate.personal.full_name}\n"
        f"Candidate headline: {candidate.personal.headline or ''}\n"
        f"Job title: {job.title}\n"
        f"Job company: {job.company or ''}\n"
        f"Match score: {match_result.score}\n"
        f"Matched skills: {', '.join(match_result.matched_skills)}\n"
        f"Missing skills: {', '.join(match_result.missing_skills)}\n"
        f"Keyword hits: {', '.join(match_result.keyword_hits)}\n"
        f"Highlights: {' | '.join(match_result.highlights)}\n"
    )
