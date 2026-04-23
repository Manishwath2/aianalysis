from __future__ import annotations

import re
from datetime import date, datetime
from typing import Iterable

from app.prompts.manager import render_prompt
from app.providers.llm.base import ProviderConfigError, ProviderRequestError
from app.providers.llm.registry import registry
from app.schemas.candidate import CandidateProfile, ExperienceItem, ProjectItem
from app.schemas.chat import ChatCompletionMessage
from app.schemas.resume_requests import ResumeAIOptions


class AIEnrichmentError(Exception):
    pass


def _split_bullets(text: str) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    out: list[str] = []
    for line in lines:
        line = re.sub(r"^(\d+[\).\s]+|[-*\u2022]+\s*)", "", line).strip()
        if line:
            out.append(line)
    return out


def _take_first(items: Iterable[str], max_items: int) -> list[str]:
    return [x for x in items if x][: max_items]


def _top_skills(candidate: CandidateProfile, limit: int = 6) -> list[str]:
    out: list[str] = []
    for group in candidate.skills:
        for item in group.items:
            if item.name and item.name not in out:
                out.append(item.name)
            if len(out) >= limit:
                return out
    return out


def _full_month_start(value: str | None) -> date | None:
    if not value:
        return None
    try:
        if len(value) == 4:
            return date(int(value), 1, 1)
        if len(value) == 7:
            year, month = value.split("-")
            return date(int(year), int(month), 1)
        if len(value) == 10:
            year, month, day = value.split("-")
            return date(int(year), int(month), int(day))
    except ValueError:
        return None
    return None


def _estimate_experience_years(candidate: CandidateProfile) -> int | None:
    starts: list[date] = []
    ends: list[date] = []
    today = datetime.utcnow().date()
    for item in candidate.experience:
        if item.date_range is None:
            continue
        start = _full_month_start(item.date_range.start)
        end = today if item.date_range.is_current else _full_month_start(item.date_range.end)
        if start:
            starts.append(start)
        if end:
            ends.append(end)
    if starts and ends:
        return max(1, round((max(ends) - min(starts)).days / 365.25))
    if candidate.experience:
        return len(candidate.experience) * 2
    return None


def _recent_roles(candidate: CandidateProfile, limit: int = 2) -> str:
    values = [f"{item.role} at {item.company}" for item in candidate.experience[:limit]]
    return ", ".join([value for value in values if value])


def _heuristic_summary(candidate: CandidateProfile) -> str:
    headline = candidate.personal.headline or "Candidate profile"
    years = _estimate_experience_years(candidate)
    years_phrase = f"{years}+ years of experience" if years else "hands-on experience"
    skills = ", ".join(_top_skills(candidate)) or "relevant technical and delivery skills"
    recent = _recent_roles(candidate, limit=2)

    sentences = [
        f"{headline} with {years_phrase} delivering production work across {skills}.",
        "Builds structured backend or product workflows with an emphasis on practical execution, maintainable systems, and recruiter-safe communication.",
    ]
    if recent:
        sentences.append(f"Recent experience includes {recent}, which provides the strongest evidence for current role relevance.")
    return " ".join(sentences[:3])


def _heuristic_experience_bullets(item: ExperienceItem, max_bullets: int) -> list[str]:
    bullets: list[str] = []
    tech = ", ".join(item.technologies[:5])
    if item.summary:
        bullets.append(
            f"Led {item.role.lower()} work at {item.company}, translating business needs into reliable delivery outcomes."
        )
    if tech:
        bullets.append(f"Built and supported production features using {tech}.")
    for bullet in item.bullets:
        cleaned = bullet.strip().rstrip(".")
        if cleaned:
            bullets.append(f"{cleaned}.")
    for achievement in item.achievements:
        cleaned = achievement.strip().rstrip(".")
        if cleaned:
            bullets.append(f"Delivered measurable progress highlighted by {cleaned.lower()}.")

    if not bullets:
        bullets.append(f"Owned core responsibilities for {item.role.lower()} delivery at {item.company}.")

    return _take_first(dict.fromkeys(bullets), max_bullets)


def _heuristic_project_bullets(item: ProjectItem, max_bullets: int) -> list[str]:
    bullets: list[str] = []
    tech = ", ".join(item.technologies[:5])
    if item.description:
        bullets.append(f"Built {item.name} to {item.description.strip().rstrip('.')}.")
    if tech:
        bullets.append(f"Implemented the solution using {tech}.")
    for bullet in item.bullets:
        cleaned = bullet.strip().rstrip(".")
        if cleaned:
            bullets.append(f"{cleaned}.")
    if not bullets:
        bullets.append(f"Delivered {item.name} with clear ownership of implementation details and output quality.")
    return _take_first(dict.fromkeys(bullets), max_bullets)


async def _complete_text(prompt: str, provider: str | None, model: str | None) -> tuple[str, str, str]:
    adapter = registry.get(provider)
    messages = [ChatCompletionMessage(role="user", content=prompt)]
    try:
        text = await adapter.complete_chat(messages=messages, model=model)
    except (ProviderConfigError, ProviderRequestError) as exc:
        raise AIEnrichmentError(str(exc)) from exc
    used_model = model or adapter.default_model()
    return text, adapter.provider_name, used_model


async def _enrich_summary(candidate: CandidateProfile, options: ResumeAIOptions) -> tuple[str | None, str, str]:
    adapter = registry.get(options.provider)
    used_model = options.model or adapter.default_model()
    if adapter.provider_name == "demo":
        return _heuristic_summary(candidate), adapter.provider_name, used_model

    prompt = render_prompt("resume.summary.v1", candidate)
    text, provider, model = await _complete_text(prompt, options.provider, options.model)
    return text.strip() or None, provider, model


async def _enrich_experience_item(item: ExperienceItem, options: ResumeAIOptions) -> tuple[list[str], str, str]:
    adapter = registry.get(options.provider)
    used_model = options.model or adapter.default_model()
    if adapter.provider_name == "demo":
        return _heuristic_experience_bullets(item, options.max_bullets_per_item), adapter.provider_name, used_model

    prompt = render_prompt("resume.experience_bullets.v1", item, options.max_bullets_per_item)
    text, provider, model = await _complete_text(prompt, options.provider, options.model)
    bullets = _take_first(_split_bullets(text), options.max_bullets_per_item)
    return bullets, provider, model


async def _enrich_project_item(item: ProjectItem, options: ResumeAIOptions) -> tuple[list[str], str, str]:
    adapter = registry.get(options.provider)
    used_model = options.model or adapter.default_model()
    if adapter.provider_name == "demo":
        return _heuristic_project_bullets(item, options.max_bullets_per_item), adapter.provider_name, used_model

    prompt = render_prompt("resume.project_bullets.v1", item, options.max_bullets_per_item)
    text, provider, model = await _complete_text(prompt, options.provider, options.model)
    bullets = _take_first(_split_bullets(text), options.max_bullets_per_item)
    return bullets, provider, model


async def enrich_candidate(candidate: CandidateProfile, options: ResumeAIOptions) -> tuple[CandidateProfile, dict[str, object]]:
    enrichments = options.enrichments or ["summary"]
    enriched = candidate.model_copy(deep=True)
    used_provider: str | None = None
    used_model: str | None = None

    if "summary" in enrichments:
        should_apply = enriched.summary is None or not (enriched.summary.about or "").strip()
        if not options.apply_if_missing:
            should_apply = True
        if should_apply:
            summary_text, used_provider, used_model = await _enrich_summary(enriched, options)
            if enriched.summary is None:
                from app.schemas.candidate import SummarySection

                enriched.summary = SummarySection(about=summary_text, highlights=[])
            else:
                enriched.summary.about = summary_text

    if "experience_bullets" in enrichments and enriched.experience:
        for idx, exp in enumerate(enriched.experience):
            if options.apply_if_missing and exp.bullets:
                continue
            bullets, used_provider, used_model = await _enrich_experience_item(exp, options)
            enriched.experience[idx].bullets = bullets

    if "project_bullets" in enrichments and enriched.projects:
        for idx, proj in enumerate(enriched.projects):
            if options.apply_if_missing and proj.bullets:
                continue
            bullets, used_provider, used_model = await _enrich_project_item(proj, options)
            enriched.projects[idx].bullets = bullets

    provenance = {
        "ai_used": True,
        "ai_provider": used_provider,
        "ai_model": used_model,
        "ai_enrichments": enrichments,
    }
    return enriched, provenance


async def generate_summary(
    candidate: CandidateProfile,
    *,
    provider: str | None = None,
    model: str | None = None,
) -> tuple[str | None, str, str]:
    options = ResumeAIOptions(provider=provider, model=model)
    return await _enrich_summary(candidate, options)


async def enhance_experience_bullets(
    item: ExperienceItem,
    *,
    max_bullets: int = 3,
    provider: str | None = None,
    model: str | None = None,
) -> tuple[list[str], str, str]:
    options = ResumeAIOptions(provider=provider, model=model, max_bullets_per_item=max_bullets)
    return await _enrich_experience_item(item, options)


async def enhance_project_bullets(
    item: ProjectItem,
    *,
    max_bullets: int = 3,
    provider: str | None = None,
    model: str | None = None,
) -> tuple[list[str], str, str]:
    options = ResumeAIOptions(provider=provider, model=model, max_bullets_per_item=max_bullets)
    return await _enrich_project_item(item, options)
