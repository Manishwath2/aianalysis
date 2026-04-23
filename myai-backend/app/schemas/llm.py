from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


LLMProvider = Literal["gemini", "openwebui", "demo"]
ProviderStatus = Literal["planned", "available", "down"]


class LLMProviderInfo(BaseModel):
    provider: LLMProvider
    display_name: str
    status: ProviderStatus = "planned"


class LLMProvidersResponse(BaseModel):
    providers: list[LLMProviderInfo]


class LLMModel(BaseModel):
    id: str = Field(min_length=1, max_length=200)
    provider: LLMProvider
    display_name: str


class LLMProviderHealth(BaseModel):
    provider: LLMProvider
    status: ProviderStatus
    detail: str | None = None

