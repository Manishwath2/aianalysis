from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.candidate import CandidateProfile
from app.schemas.job import JobDescription


class ChatSessionCreateResponse(BaseModel):
    session_id: str


class ChatMessageCreateRequest(BaseModel):
    role: Literal["system", "user", "assistant"] = "user"
    content: str = Field(min_length=1, max_length=8000)
    tool: str | None = None
    candidate_id: str | None = None


class ChatStreamRequest(BaseModel):
    message: str = Field(default="", max_length=8000)
    tool: str | None = None
    provider: str | None = None
    model: str | None = None
    candidate_id: str | None = None


class ResumeChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    candidate_id: str | None = None
    candidate: CandidateProfile | None = None
    job_id: str | None = None
    job: JobDescription | None = None
    template_id: str | None = Field(default=None, min_length=1, max_length=60)
    provider: str | None = None
    model: str | None = None


class ResumeChatResponse(BaseModel):
    answer: str
    provider: str
    model: str


class ChatCompletionMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)


class ChatCompletionsRequest(BaseModel):
    model: str | None = None
    provider: str | None = None
    messages: list[ChatCompletionMessage] = Field(default_factory=list)
    stream: bool = False


class ChatCompletionsChoiceMessage(BaseModel):
    role: Literal["assistant"] = "assistant"
    content: str


class ChatCompletionsChoice(BaseModel):
    index: int = 0
    message: ChatCompletionsChoiceMessage
    finish_reason: Literal["stop"] = "stop"


class ChatCompletionsUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletionsResponse(BaseModel):
    id: str
    object: Literal["chat.completion"] = "chat.completion"
    created: int
    model: str
    choices: list[ChatCompletionsChoice]
    usage: ChatCompletionsUsage


class ModelsResponseItem(BaseModel):
    id: str
    object: Literal["model"] = "model"
    created: int
    owned_by: str


class ModelsResponse(BaseModel):
    object: Literal["list"] = "list"
    data: list[ModelsResponseItem]


def utc_timestamp(value: datetime | None = None) -> int:
    dt = value or datetime.utcnow()
    return int(dt.timestamp())

