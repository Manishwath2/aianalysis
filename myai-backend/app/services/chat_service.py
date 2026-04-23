from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.prompts.manager import render_prompt
from app.providers.llm.base import ProviderConfigError, ProviderRequestError
from app.providers.llm.registry import registry
from app.schemas.candidate import CandidateProfile
from app.schemas.chat import ChatCompletionMessage
from app.schemas.job import JobDescription
from app.schemas.llm import LLMModel
from app.services.job_service import JobResolutionError, resolve_job
from app.services.matching_service import compute_match_result
from app.services.resume_service import CandidateResolutionError, resolve_candidate


class ChatServiceError(Exception):
    pass


async def list_provider_models(provider: str | None) -> list[LLMModel]:
    adapter = registry.get(provider)
    try:
        return await adapter.list_models()
    except (ProviderConfigError, ProviderRequestError) as exc:
        raise ChatServiceError(str(exc)) from exc


async def complete_messages(
    *,
    messages: list[ChatCompletionMessage],
    provider: str | None,
    model: str | None,
) -> tuple[str, str, str]:
    adapter = registry.get(provider)
    try:
        text = await adapter.complete_chat(messages=messages, model=model)
    except (ProviderConfigError, ProviderRequestError) as exc:
        raise ChatServiceError(str(exc)) from exc
    used_model = model or adapter.default_model()
    return text, adapter.provider_name, used_model


async def stream_messages(
    *,
    messages: list[ChatCompletionMessage],
    provider: str | None,
    model: str | None,
) -> AsyncIterator[tuple[str, str, str]]:
    adapter = registry.get(provider)
    used_model = model or adapter.default_model()
    try:
        async for token in adapter.stream_chat(messages=messages, model=model):
            yield token, adapter.provider_name, used_model
    except (ProviderConfigError, ProviderRequestError) as exc:
        raise ChatServiceError(str(exc)) from exc


def _top_candidate_skills(candidate: CandidateProfile, limit: int = 6) -> list[str]:
    skills: list[str] = []
    for group in candidate.skills:
        for item in group.items:
            if item.name and item.name not in skills:
                skills.append(item.name)
            if len(skills) >= limit:
                return skills
    return skills


def _fallback_resume_help(
    *,
    message: str,
    candidate: CandidateProfile | None,
    job: JobDescription | None,
    template_id: str | None,
) -> str:
    lowered = message.lower()

    if candidate is not None and job is not None:
        result = compute_match_result(candidate, job)
        matched = ", ".join(result.matched_skills[:4]) or "relevant transferable skills"
        missing = ", ".join(result.missing_skills[:2]) or "no major must-have gaps identified"
        if any(word in lowered for word in ("shortlist", "rank", "fit", "match", "hire")):
            return (
                f"{candidate.personal.full_name} scores {result.score}/100 for {job.title} and currently lands in the "
                f"'{result.band}' band. The strongest alignment is around {matched}. "
                f"The main watch-out is {missing}. Shortlist this profile if the hiring team values the matched stack more than the current gaps."
            )
        return (
            f"For {job.title}, the candidate shows the strongest evidence in {matched}. "
            f"Recent experience and the current profile support a {result.band}-fit assessment with a score of {result.score}/100. "
            f"The main area to validate in screening is {missing}."
        )

    if candidate is not None:
        skills = ", ".join(_top_candidate_skills(candidate)) or "the listed backend and domain skills"
        latest_role = candidate.experience[0].role if candidate.experience else candidate.personal.headline or "the current profile"
        if any(word in lowered for word in ("summary", "resume", "rewrite")):
            return (
                f"Focus the resume on {latest_role}, emphasizing {skills}. "
                f"Keep the summary concise, evidence-based, and tied to delivery scope, backend ownership, and business impact. "
                f"Use the strongest recent role and the clearest technologies as the opening proof points."
            )
        return (
            f"The selected candidate is best positioned around {skills}. "
            f"Lead with the most recent role, {latest_role}, then support it with the strongest project or delivery evidence. "
            f"If you want sharper recruiter output, ask for a summary rewrite, shortlist reasoning, or template JSON guidance."
        )

    if job is not None:
        must_have = ", ".join(job.must_have_skills[:5]) or "the listed requirements"
        return (
            f"The current job is centered on {must_have}. "
            f"For accurate shortlisting, prioritize must-have skill coverage first, then validate years of experience, seniority, and adjacent domain evidence. "
            f"If you attach a candidate context, I can explain fit and shortlist readiness more precisely."
        )

    template_note = f" Target template: {template_id}." if template_id else ""
    return (
        "Provide a candidate profile, a job description, or both for grounded recruiter guidance."
        f"{template_note} I can then help with summaries, shortlist logic, recruiter notes, and template-ready output."
    )


async def complete_resume_help(
    *,
    message: str,
    candidate: CandidateProfile | None,
    candidate_id: str | None,
    job: JobDescription | None,
    job_id: str | None,
    template_id: str | None,
    provider: str | None,
    model: str | None,
    session: AsyncSession | None,
) -> tuple[str, str, str]:
    resolved_candidate: CandidateProfile | None = None
    if candidate is not None or candidate_id:
        try:
            resolved_candidate = await resolve_candidate(
                session=session,
                candidate=candidate,
                candidate_id=candidate_id,
            )
        except CandidateResolutionError as exc:
            raise ChatServiceError(str(exc)) from exc
    resolved_job: JobDescription | None = None
    if job is not None or job_id:
        try:
            resolved_job = await resolve_job(session=session, job=job, job_id=job_id)
        except JobResolutionError as exc:
            raise ChatServiceError(str(exc)) from exc

    adapter = registry.get(provider)
    used_model = model or adapter.default_model()
    if adapter.provider_name == "demo":
        return (
            _fallback_resume_help(
                message=message,
                candidate=resolved_candidate,
                job=resolved_job,
                template_id=template_id,
            ),
            adapter.provider_name,
            used_model,
        )

    messages: list[ChatCompletionMessage] = [
        ChatCompletionMessage(
            role="system",
            content=render_prompt("chat.resume.system.v1"),
        )
    ]
    if resolved_candidate is not None:
        messages.append(
            ChatCompletionMessage(
                role="system",
                content=render_prompt(
                    "chat.resume.context.v1",
                    resolved_candidate,
                    template_id=template_id,
                ),
            )
        )
    if resolved_job is not None:
        messages.append(
            ChatCompletionMessage(
                role="system",
                content=render_prompt("chat.job.context.v1", resolved_job),
            )
        )

    messages.append(ChatCompletionMessage(role="user", content=message))

    try:
        return await complete_messages(messages=messages, provider=provider, model=model)
    except ChatServiceError:
        fallback = _fallback_resume_help(
            message=message,
            candidate=resolved_candidate,
            job=resolved_job,
            template_id=template_id,
        )
        return fallback, "demo", "demo/fallback"
