from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.providers.llm.registry import registry
from app.schemas.chat import ModelsResponse, ModelsResponseItem, utc_timestamp
from app.schemas.llm import LLMModel, LLMProvidersResponse
from app.services.chat_service import ChatServiceError, list_provider_models

router = APIRouter()


@router.get("/llm/providers", response_model=LLMProvidersResponse)
def list_providers() -> LLMProvidersResponse:
    return LLMProvidersResponse(providers=registry.list_infos())


@router.get("/llm/models", response_model=list[LLMModel])
async def list_models(provider: str | None = None) -> list[LLMModel]:
    try:
        chosen = provider or registry.get(None).provider_name
        return await list_provider_models(chosen)
    except ChatServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/models", response_model=ModelsResponse)
async def list_models_openai(provider: str | None = None) -> ModelsResponse:
    chosen = provider or registry.get(None).provider_name
    try:
        models = await list_provider_models(chosen)
    except ChatServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    created = utc_timestamp()
    return ModelsResponse(
        data=[
            ModelsResponseItem(id=m.id, created=created, owned_by=m.provider)
            for m in models
        ]
    )

