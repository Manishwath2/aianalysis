from __future__ import annotations

from typing import Iterable

from app.schemas.candidate import CandidateProfile
from app.schemas.job import JobDescription


def _join_non_empty(values: Iterable[str]) -> str:
    return ", ".join(value for value in values if value and value.strip())


def build_resume_chat_system_prompt() -> str:
    return (
        "You are an AI Recruitment Assistant for recruiter workflows. "
        "Help with resume quality, job-fit analysis, candidate shortlisting, recruiter notes, and template-ready resume output. "
        "Keep answers concise, evidence-based, and directly usable in a frontend UI. "
        "Never invent candidate experience, metrics, skills, employers, or project outcomes. "
        "If the provided data is incomplete, say what is missing and make the safest practical recommendation."
    )


def build_candidate_context_prompt(candidate: CandidateProfile, template_id: str | None = None) -> str:
    skills: list[str] = []
    for group in candidate.skills:
        skills.extend(item.name for item in group.items if item.name)

    experience = _join_non_empty(
        f"{item.role} at {item.company}" for item in candidate.experience[:4]
    )
    projects = _join_non_empty(item.name for item in candidate.projects[:4])
    education = _join_non_empty(
        f"{item.degree or 'Education'} at {item.school}" for item in candidate.education[:2]
    )

    lines = [
        "Candidate profile context:",
        f"Name: {candidate.personal.full_name}",
        f"Headline: {candidate.personal.headline or ''}",
        f"Location: {candidate.personal.location or ''}",
        f"Summary: {candidate.summary.about if candidate.summary and candidate.summary.about else ''}",
        f"Skills: {_join_non_empty(skills[:15])}",
        f"Experience: {experience}",
        f"Projects: {projects}",
        f"Education: {education}",
    ]
    if template_id:
        lines.append(f"Target template: {template_id}")
    return "\n".join(lines)


def build_job_context_prompt(job: JobDescription) -> str:
    return "\n".join(
        [
            "Job description context:",
            f"Title: {job.title}",
            f"Company: {job.company or ''}",
            f"Location: {job.location or ''}",
            f"Summary: {job.summary or ''}",
            f"Must-have skills: {_join_non_empty(job.must_have_skills)}",
            f"Nice-to-have skills: {_join_non_empty(job.nice_to_have_skills)}",
            f"Keywords: {_join_non_empty(job.keywords)}",
            f"Minimum years experience: {job.minimum_years_experience or ''}",
            f"Seniority: {job.seniority or ''}",
        ]
    )
