from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from math import ceil

from sqlalchemy.ext.asyncio import AsyncSession

from app.prompts.manager import render_prompt
from app.providers.llm.base import ProviderConfigError, ProviderRequestError
from app.providers.llm.registry import registry
from app.schemas.candidate import CandidateProfile
from app.schemas.chat import ChatCompletionMessage
from app.schemas.job import JobDescription
from app.schemas.matching import (
    CandidateMatchRequest,
    CandidateMatchResponse,
    CandidateMatchResult,
    CandidateRankingRequest,
    CandidateRankingResponse,
    MatchScoreBreakdown,
    RecruiterAIOptions,
    RecruiterSummaryRequest,
    RecruiterSummaryResponse,
)
from app.services.candidate_service import CandidateNotFoundError, get_candidate, list_candidates
from app.services.job_service import JobResolutionError, resolve_job


TOKEN_RE = re.compile(r"[a-z0-9+#]{2,}")

STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "be",
    "build",
    "building",
    "by",
    "candidate",
    "create",
    "deliver",
    "design",
    "for",
    "from",
    "good",
    "have",
    "in",
    "is",
    "of",
    "on",
    "or",
    "role",
    "strong",
    "team",
    "the",
    "to",
    "using",
    "with",
    "work",
    "years",
}

SKILL_ALIASES = {
    "ci cd": "cicd",
    "ci/cd": "cicd",
    "docker containers": "docker",
    "generative ai": "genai",
    "github actions": "github_actions",
    "large language model": "llm",
    "large language models": "llm",
    "llms": "llm",
    "machine learning": "ml",
    "next js": "nextjs",
    "next.js": "nextjs",
    "node js": "nodejs",
    "node.js": "nodejs",
    "postgres": "postgresql",
    "postgres sql": "postgresql",
    "prompt engineering": "prompt_engineering",
    "rest api": "rest_api",
    "rest apis": "rest_api",
    "restful api": "rest_api",
    "restful apis": "rest_api",
}

SENIORITY_MAP = {
    "intern": 0,
    "junior": 1,
    "associate": 1,
    "mid": 2,
    "senior": 3,
    "lead": 4,
    "staff": 4,
    "manager": 5,
    "principal": 5,
}


class MatchingServiceError(Exception):
    pass


class CandidateResolutionError(MatchingServiceError):
    pass


@dataclass(slots=True)
class CandidateEvidence:
    skill_keys: set[str]
    skill_tokens: set[str]
    terms: set[str]
    project_terms: set[str]


def _clean_text(value: str) -> str:
    text = value.lower().strip()
    text = text.replace("&", " and ")
    text = text.replace("/", " ")
    text = text.replace("-", " ")
    text = re.sub(r"\s+", " ", text)
    return text


def _normalize_phrase(value: str) -> str:
    cleaned = _clean_text(value)
    cleaned = re.sub(r"[^a-z0-9+#.\s]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return ""
    return SKILL_ALIASES.get(cleaned, cleaned)


def _significant_tokens(value: str) -> set[str]:
    cleaned = _clean_text(value)
    tokens = {token for token in TOKEN_RE.findall(cleaned) if token not in STOPWORDS}
    normalized = {_normalize_phrase(token) for token in tokens}
    normalized.discard("")
    tokens.update(normalized)
    return tokens


def _phrase_features(value: str) -> tuple[str, set[str]]:
    key = _normalize_phrase(value)
    tokens = _significant_tokens(value)
    if key:
        tokens.add(key)
        if "_" in key:
            tokens.update(part for part in key.split("_") if part)
    return key, tokens


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


def _estimate_experience_years(candidate: CandidateProfile) -> float:
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
        days = max((max(ends) - min(starts)).days, 0)
        return round(days / 365.25, 1)

    if candidate.experience:
        return round(len(candidate.experience) * 1.5, 1)
    return 0.0


def _candidate_evidence(candidate: CandidateProfile) -> CandidateEvidence:
    skill_keys: set[str] = set()
    skill_tokens: set[str] = set()
    terms: set[str] = set()
    project_terms: set[str] = set()

    def add_text(text: str | None, *, project: bool = False) -> None:
        if not text:
            return
        tokens = _significant_tokens(text)
        terms.update(tokens)
        if project:
            project_terms.update(tokens)

    for raw in [candidate.personal.full_name, candidate.personal.headline or "", candidate.personal.location or ""]:
        add_text(raw)

    if candidate.summary and candidate.summary.about:
        add_text(candidate.summary.about)
    if candidate.summary:
        for highlight in candidate.summary.highlights:
            add_text(highlight)

    for group in candidate.skills:
        add_text(group.category)
        for item in group.items:
            key, tokens = _phrase_features(item.name)
            if key:
                skill_keys.add(key)
            skill_tokens.update(tokens)
            terms.update(tokens)
            for keyword in item.keywords:
                key, keyword_tokens = _phrase_features(keyword)
                if key:
                    skill_keys.add(key)
                skill_tokens.update(keyword_tokens)
                terms.update(keyword_tokens)

    for experience in candidate.experience:
        add_text(experience.company)
        add_text(experience.role)
        add_text(experience.summary)
        for bullet in experience.bullets:
            add_text(bullet)
        for achievement in experience.achievements:
            add_text(achievement)
        for tech in experience.technologies:
            key, tokens = _phrase_features(tech)
            if key:
                skill_keys.add(key)
            skill_tokens.update(tokens)
            terms.update(tokens)

    for project in candidate.projects:
        add_text(project.name, project=True)
        add_text(project.description, project=True)
        for bullet in project.bullets:
            add_text(bullet, project=True)
        for tech in project.technologies:
            key, tokens = _phrase_features(tech)
            if key:
                skill_keys.add(key)
                project_terms.add(key)
            skill_tokens.update(tokens)
            terms.update(tokens)
            project_terms.update(tokens)

    terms.update(skill_keys)
    terms.update(skill_tokens)
    return CandidateEvidence(
        skill_keys=skill_keys,
        skill_tokens=skill_tokens,
        terms=terms,
        project_terms=project_terms,
    )


def _job_keyword_terms(job: JobDescription) -> set[str]:
    values = list(job.keywords) + list(job.responsibilities)
    if job.summary:
        values.append(job.summary)
    out: set[str] = set()
    for value in values:
        out.update(_significant_tokens(value))
    return out


def _job_reference_terms(job: JobDescription) -> set[str]:
    values = list(job.must_have_skills) + list(job.nice_to_have_skills) + list(job.keywords)
    out: set[str] = set()
    for value in values:
        key, tokens = _phrase_features(value)
        if key:
            out.add(key)
        out.update(tokens)
    return out


def _match_skill(raw_skill: str, evidence: CandidateEvidence) -> bool:
    key, tokens = _phrase_features(raw_skill)
    if key and key in evidence.skill_keys:
        return True
    if key and key in evidence.skill_tokens:
        return True
    if tokens and tokens.issubset(evidence.skill_tokens):
        return True
    return False


def _match_skill_list(skills: list[str], evidence: CandidateEvidence) -> tuple[list[str], list[str]]:
    matched: list[str] = []
    missing: list[str] = []
    seen: set[str] = set()
    for raw_skill in skills:
        label = raw_skill.strip()
        if not label:
            continue
        dedupe_key = label.lower()
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        if _match_skill(label, evidence):
            matched.append(label)
        else:
            missing.append(label)
    return matched, missing


def _safe_ratio(matched: int, total: int, *, empty_value: float = 1.0) -> float:
    if total <= 0:
        return empty_value
    return matched / total


def _estimate_candidate_seniority(candidate: CandidateProfile, experience_years: float) -> int:
    values: list[str] = []
    if candidate.personal.headline:
        values.append(candidate.personal.headline.lower())
    values.extend(item.role.lower() for item in candidate.experience if item.role)

    text = " ".join(values)
    for keyword, rank in sorted(SENIORITY_MAP.items(), key=lambda item: item[1], reverse=True):
        if keyword in text:
            return rank

    if experience_years >= 10:
        return 5
    if experience_years >= 7:
        return 4
    if experience_years >= 4:
        return 3
    if experience_years >= 2:
        return 2
    if experience_years > 0:
        return 1
    return 0


def _required_seniority_rank(job: JobDescription) -> int | None:
    if not job.seniority:
        return None
    return SENIORITY_MAP.get(job.seniority)


def compute_match_result(candidate: CandidateProfile, job: JobDescription) -> CandidateMatchResult:
    evidence = _candidate_evidence(candidate)
    matched_required, missing_required = _match_skill_list(job.must_have_skills, evidence)
    matched_optional, _ = _match_skill_list(job.nice_to_have_skills, evidence)

    keyword_terms = _job_keyword_terms(job)
    keyword_hits = sorted(keyword_terms & evidence.terms)
    keyword_score = round(_safe_ratio(len(keyword_hits), len(keyword_terms)) * 100, 1) if keyword_terms else 100.0

    required_coverage = _safe_ratio(len(matched_required), len(job.must_have_skills))
    optional_coverage = _safe_ratio(len(matched_optional), len(job.nice_to_have_skills))
    skill_score = (required_coverage * 80) + (optional_coverage * 20)

    reference_terms = _job_reference_terms(job)
    if candidate.projects and reference_terms:
        project_overlap = len(reference_terms & evidence.project_terms)
        project_score = _safe_ratio(project_overlap, len(reference_terms), empty_value=0.0) * 100
        skill_score = (skill_score * 0.9) + (project_score * 0.1)

    experience_years = _estimate_experience_years(candidate)
    if job.minimum_years_experience is None or job.minimum_years_experience <= 0:
        experience_score = 100.0 if experience_years >= 1 else 70.0
    else:
        experience_score = min(100.0, (experience_years / job.minimum_years_experience) * 100)

    required_seniority = _required_seniority_rank(job)
    candidate_seniority = _estimate_candidate_seniority(candidate, experience_years)
    if required_seniority is None:
        seniority_score = 100.0
    else:
        diff = candidate_seniority - required_seniority
        if diff >= 0:
            seniority_score = 100.0
        elif diff == -1:
            seniority_score = 72.0
        else:
            seniority_score = 40.0

    total = (
        (skill_score * 0.55)
        + (keyword_score * 0.15)
        + (experience_score * 0.20)
        + (seniority_score * 0.10)
    )

    if job.must_have_skills and missing_required:
        missing_ratio = len(missing_required) / len(job.must_have_skills)
        total *= max(0.55, 1 - (missing_ratio * 0.45))
        if required_coverage < 0.5:
            total = min(total, 64.9)
        elif len(missing_required) >= ceil(len(job.must_have_skills) / 2):
            total = min(total, 69.9)

    if job.minimum_years_experience and experience_years < (job.minimum_years_experience * 0.75):
        total = min(total, 74.9)

    total = round(min(max(total, 0), 100), 1)
    skill_score = round(min(max(skill_score, 0), 100), 1)

    if total >= 82:
        band = "strong"
    elif total >= 68:
        band = "good"
    elif total >= 50:
        band = "moderate"
    else:
        band = "weak"

    highlights: list[str] = []
    if candidate.personal.headline:
        highlights.append(candidate.personal.headline)
    if matched_required:
        highlights.append(f"Matches must-have skills: {', '.join(matched_required[:4])}")
    elif matched_optional:
        highlights.append(f"Relevant adjacent skills: {', '.join(matched_optional[:4])}")
    if candidate.experience:
        latest = candidate.experience[0]
        highlights.append(f"Recent role: {latest.role} at {latest.company}")
    if candidate.projects and reference_terms & evidence.project_terms:
        highlights.append("Project evidence aligns with target stack and domain")
    if missing_required:
        highlights.append(f"Main gaps: {', '.join(missing_required[:3])}")

    return CandidateMatchResult(
        candidate_id=str(candidate.candidate_id),
        candidate_name=candidate.personal.full_name,
        score=total,
        band=band,
        breakdown=MatchScoreBreakdown(
            skill_score=skill_score,
            keyword_score=keyword_score,
            experience_score=round(experience_score, 1),
            seniority_score=round(seniority_score, 1),
        ),
        matched_skills=matched_required + [skill for skill in matched_optional if skill not in matched_required],
        missing_skills=missing_required,
        keyword_hits=keyword_hits[:12],
        experience_years=experience_years,
        highlights=highlights[:4],
    )


async def _resolve_candidate(
    *,
    session: AsyncSession | None,
    candidate: CandidateProfile | None,
    candidate_id: str | None,
) -> CandidateProfile:
    if candidate is not None:
        return candidate
    if not candidate_id:
        raise CandidateResolutionError("Provide candidate or candidate_id")
    try:
        return await get_candidate(session, candidate_id)
    except CandidateNotFoundError as exc:
        raise CandidateResolutionError(str(exc)) from exc


def _fallback_recruiter_summary(candidate: CandidateProfile, job: JobDescription, result: CandidateMatchResult) -> str:
    strengths = ", ".join(result.matched_skills[:4]) or "relevant transferable skills"
    risk = ", ".join(result.missing_skills[:2]) or "limited evidence for some role-specific detail"
    company = f" for {job.company}" if job.company else ""
    return (
        f"{candidate.personal.full_name} is a {result.band} fit for the {job.title} role{company}, "
        f"scoring {result.score} out of 100. The strongest evidence is around {strengths}, "
        f"supported by recent experience and aligned project or delivery signals. "
        f"The main watch-out is {risk}."
    )


async def _ai_recruiter_summary(
    candidate: CandidateProfile,
    job: JobDescription,
    result: CandidateMatchResult,
    options: RecruiterAIOptions | None,
) -> tuple[str, str | None, str | None]:
    if options is not None and not options.enabled:
        return _fallback_recruiter_summary(candidate, job, result), None, None

    adapter = registry.get(options.provider if options else None)
    if adapter.provider_name == "demo":
        return _fallback_recruiter_summary(candidate, job, result), adapter.provider_name, adapter.default_model()

    prompt = render_prompt("recruitment.recruiter_summary.v1", candidate, job, result)
    try:
        text = await adapter.complete_chat(
            messages=[ChatCompletionMessage(role="user", content=prompt)],
            model=options.model if options else None,
        )
        if text.strip():
            used_model = options.model if options and options.model else adapter.default_model()
            return text.strip(), adapter.provider_name, used_model
    except (ProviderConfigError, ProviderRequestError):
        pass

    return _fallback_recruiter_summary(candidate, job, result), None, None


async def score_candidate_against_job(
    payload: CandidateMatchRequest,
    *,
    session: AsyncSession | None,
) -> CandidateMatchResponse:
    candidate = await _resolve_candidate(
        session=session,
        candidate=payload.candidate,
        candidate_id=payload.candidate_id,
    )
    try:
        job = await resolve_job(session=session, job=payload.job, job_id=payload.job_id)
    except JobResolutionError as exc:
        raise MatchingServiceError(str(exc)) from exc

    result = compute_match_result(candidate, job)
    summary, _, _ = await _ai_recruiter_summary(candidate, job, result, payload.summary_options)
    result.recruiter_summary = summary
    return CandidateMatchResponse(job_id=str(job.job_id), result=result)


async def rank_candidates_for_job(
    payload: CandidateRankingRequest,
    *,
    session: AsyncSession | None,
) -> CandidateRankingResponse:
    try:
        job = await resolve_job(session=session, job=payload.job, job_id=payload.job_id)
    except JobResolutionError as exc:
        raise MatchingServiceError(str(exc)) from exc

    candidates: list[CandidateProfile] = []
    for candidate_id in payload.candidate_ids:
        candidates.append(await _resolve_candidate(session=session, candidate=None, candidate_id=candidate_id))
    candidates.extend(payload.candidates)

    if not candidates:
        candidates = await list_candidates(session)
    if not candidates:
        raise MatchingServiceError("No candidates available")

    ranked = [compute_match_result(candidate, job) for candidate in candidates]
    ranked.sort(key=lambda item: (-item.score, item.candidate_name.lower()))
    ranked = ranked[: payload.top_k]

    if payload.include_recruiter_summary:
        candidates_by_id = {str(item.candidate_id): item for item in candidates}
        for result in ranked:
            candidate = candidates_by_id.get(result.candidate_id)
            if candidate is None:
                continue
            summary, _, _ = await _ai_recruiter_summary(candidate, job, result, payload.summary_options)
            result.recruiter_summary = summary

    return CandidateRankingResponse(
        job_id=str(job.job_id),
        job_title=job.title,
        total_candidates=len(candidates),
        ranked_candidates=ranked,
    )


async def generate_recruiter_summary(
    payload: RecruiterSummaryRequest,
    *,
    session: AsyncSession | None,
) -> RecruiterSummaryResponse:
    candidate = await _resolve_candidate(
        session=session,
        candidate=payload.candidate,
        candidate_id=payload.candidate_id,
    )
    try:
        job = await resolve_job(session=session, job=payload.job, job_id=payload.job_id)
    except JobResolutionError as exc:
        raise MatchingServiceError(str(exc)) from exc

    result = payload.match_result or compute_match_result(candidate, job)
    summary, provider, model = await _ai_recruiter_summary(candidate, job, result, payload.options)
    return RecruiterSummaryResponse(summary=summary, provider=provider, model=model)
