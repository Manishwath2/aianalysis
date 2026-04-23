from __future__ import annotations

from typing import Iterable

from app.schemas.candidate import CandidateProfile, ExperienceItem, ProjectItem


def _join_non_empty(values: Iterable[str]) -> str:
    return ", ".join([v for v in values if v and v.strip()])


def build_summary_prompt(candidate: CandidateProfile) -> str:
    personal = candidate.personal
    headline = personal.headline or ""
    location = personal.location or ""
    skills = []
    for group in candidate.skills:
        skills.extend([item.name for item in group.items if item.name])
    skill_line = _join_non_empty(skills[:12])

    exp_bits = []
    for exp in candidate.experience[:3]:
        exp_bits.append(f"{exp.role} at {exp.company}")
    exp_line = _join_non_empty(exp_bits)

    prompt = (
        "Write a recruiter-grade resume summary in exactly 3 sentences.\n"
        "Rules:\n"
        "- Do not use first-person pronouns.\n"
        "- Do not invent employers, metrics, awards, or domain experience not present in the input.\n"
        "- Lead with role identity and scope, then mention strongest technical or delivery strengths.\n"
        "- Keep the tone professional, concise, and safe for direct resume use.\n\n"
        "Candidate data:\n"
        f"Name: {personal.full_name}\n"
        f"Headline: {headline}\n"
        f"Location: {location}\n"
        f"Experience snapshot: {exp_line}\n"
        f"Top skills: {skill_line}\n"
    )
    return prompt


def build_experience_bullets_prompt(item: ExperienceItem, max_bullets: int) -> str:
    tech = _join_non_empty(item.technologies)
    achievements = _join_non_empty(item.achievements)
    summary = item.summary or ""
    prompt = (
        f"Write {max_bullets} high-quality resume bullets for this experience entry.\n"
        "Rules:\n"
        "- Each bullet must start with a strong action verb.\n"
        "- Prefer 14 to 24 words per bullet.\n"
        "- Include tools, scope, and outcome when evidence exists.\n"
        "- Do not invent numbers, percentages, scale, or business impact.\n"
        "- Return only the bullets, one per line, with no heading.\n\n"
        f"Role: {item.role}\n"
        f"Company: {item.company}\n"
        f"Summary: {summary}\n"
        f"Technologies: {tech}\n"
        f"Achievements: {achievements}\n"
    )
    return prompt


def build_project_bullets_prompt(item: ProjectItem, max_bullets: int) -> str:
    tech = _join_non_empty(item.technologies)
    prompt = (
        f"Write {max_bullets} high-quality resume bullets for this project.\n"
        "Rules:\n"
        "- Highlight what was built, how it was implemented, and why it matters.\n"
        "- Mention concrete technologies when useful.\n"
        "- Do not invent users, metrics, scale, or outcomes not supported by the input.\n"
        "- Return only the bullets, one per line, with no heading.\n\n"
        f"Project: {item.name}\n"
        f"Description: {item.description or ''}\n"
        f"Technologies: {tech}\n"
    )
    return prompt
