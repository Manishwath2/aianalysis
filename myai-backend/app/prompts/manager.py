from __future__ import annotations

from typing import Callable

from app.prompts.chat import (
    build_candidate_context_prompt,
    build_job_context_prompt,
    build_resume_chat_system_prompt,
)
from app.prompts.recruitment import build_recruiter_summary_prompt
from app.prompts.resume import (
    build_experience_bullets_prompt,
    build_project_bullets_prompt,
    build_summary_prompt,
)

PromptBuilder = Callable[..., str]

PROMPT_REGISTRY: dict[str, PromptBuilder] = {
    "chat.resume.context.v1": build_candidate_context_prompt,
    "chat.job.context.v1": build_job_context_prompt,
    "chat.resume.system.v1": build_resume_chat_system_prompt,
    "recruitment.recruiter_summary.v1": build_recruiter_summary_prompt,
    "resume.summary.v1": build_summary_prompt,
    "resume.experience_bullets.v1": build_experience_bullets_prompt,
    "resume.project_bullets.v1": build_project_bullets_prompt,
}


def get_prompt(name: str) -> PromptBuilder:
    if name not in PROMPT_REGISTRY:
        raise KeyError(f"Unknown prompt: {name}")
    return PROMPT_REGISTRY[name]


def render_prompt(name: str, *args, **kwargs) -> str:
    builder = get_prompt(name)
    return builder(*args, **kwargs)
