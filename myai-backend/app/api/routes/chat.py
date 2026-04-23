from __future__ import annotations

import json
from collections.abc import AsyncIterator
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import optional_db_session
from app.schemas.chat import (
    ChatCompletionMessage,
    ChatCompletionsChoice,
    ChatCompletionsChoiceMessage,
    ChatCompletionsRequest,
    ChatCompletionsResponse,
    ChatCompletionsUsage,
    ChatMessageCreateRequest,
    ResumeChatRequest,
    ResumeChatResponse,
    ChatSessionCreateResponse,
    ChatStreamRequest,
)
from app.services.chat_service import (
    ChatServiceError,
    complete_messages,
    complete_resume_help,
    stream_messages,
)
from app.utils.ids import new_uuid
from app.utils.memory_store import CHAT_MESSAGES, CHAT_SESSIONS

router = APIRouter()


@router.post("/chat/sessions", response_model=ChatSessionCreateResponse)
def create_session() -> ChatSessionCreateResponse:
    session_id = str(new_uuid())
    CHAT_SESSIONS.add(session_id)
    CHAT_MESSAGES[session_id] = []
    return ChatSessionCreateResponse(session_id=session_id)


@router.post("/chat/sessions/{session_id}/messages")
def add_message(session_id: str, payload: ChatMessageCreateRequest) -> dict:
    if session_id not in CHAT_SESSIONS:
        CHAT_SESSIONS.add(session_id)
        CHAT_MESSAGES[session_id] = []

    CHAT_MESSAGES[session_id].append(payload)
    return {"ok": True}


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _provider_stream(messages: list[ChatCompletionMessage], provider: str | None, model: str | None) -> AsyncIterator[str]:
    mode = "thinking"
    try:
        first = True
        async for token, used_provider, used_model in stream_messages(messages=messages, provider=provider, model=model):
            if first:
                first = False
                yield _sse("meta", {"provider": used_provider, "model": used_model, "mode": mode})
            yield _sse("delta", {"text": token})
        yield _sse("done", {"ok": True})
    except ChatServiceError as exc:
        yield _sse("error", {"detail": str(exc)})
        yield _sse("done", {"ok": False})


@router.post("/chat/sessions/{session_id}/stream")
def stream_assistant(session_id: str, payload: ChatStreamRequest):
    prompt = payload.message or ""
    messages = [ChatCompletionMessage(role="user", content=prompt)]

    return StreamingResponse(
        _provider_stream(messages=messages, provider=payload.provider, model=payload.model),
        media_type="text/event-stream",
        headers={"cache-control": "no-cache", "x-accel-buffering": "no"},
    )


@router.post("/chat/completions", response_model=ChatCompletionsResponse)
async def chat_completions(payload: ChatCompletionsRequest) -> ChatCompletionsResponse:
    if payload.stream:
        raise HTTPException(status_code=400, detail="Use /v1/chat/sessions/{session_id}/stream for SSE streaming")
    if not payload.messages:
        raise HTTPException(status_code=400, detail="messages are required")

    try:
        text, used_provider, used_model = await complete_messages(
            messages=payload.messages,
            provider=payload.provider,
            model=payload.model,
        )
    except ChatServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    created = int(datetime.utcnow().timestamp())
    completion_id = f"chatcmpl_{new_uuid()}"
    completion_tokens = max(1, len(text.split())) if text else 0
    prompt_tokens = sum(len(m.content.split()) for m in payload.messages)
    usage = ChatCompletionsUsage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
    )

    return ChatCompletionsResponse(
        id=completion_id,
        created=created,
        model=f"{used_provider}:{used_model}",
        choices=[
            ChatCompletionsChoice(
                index=0,
                message=ChatCompletionsChoiceMessage(content=text),
                finish_reason="stop",
            )
        ],
        usage=usage,
    )


@router.post("/chat/resume-help", response_model=ResumeChatResponse)
async def resume_help(
    payload: ResumeChatRequest,
    session: AsyncSession | None = Depends(optional_db_session),
) -> ResumeChatResponse:
    try:
        answer, provider, model = await complete_resume_help(
            message=payload.message,
            candidate=payload.candidate,
            candidate_id=payload.candidate_id,
            job=payload.job,
            job_id=payload.job_id,
            template_id=payload.template_id,
            provider=payload.provider,
            model=payload.model,
            session=session,
        )
    except ChatServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return ResumeChatResponse(answer=answer, provider=provider, model=model)
