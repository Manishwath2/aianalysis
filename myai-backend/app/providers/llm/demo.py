from __future__ import annotations

from app.providers.llm.base import LLMProviderAdapter
from app.schemas.chat import ChatCompletionMessage
from app.schemas.llm import LLMModel


class DemoProvider(LLMProviderAdapter):
    provider_name = "demo"

    def is_configured(self) -> bool:
        return True

    def default_model(self) -> str:
        return "demo/default"

    async def list_models(self) -> list[LLMModel]:
        return [
            LLMModel(id="demo/default", provider="demo", display_name="Demo Model"),
        ]

    async def complete_chat(self, *, messages: list[ChatCompletionMessage], model: str | None) -> str:
        last_user = next((m.content for m in reversed(messages) if m.role == "user"), "")
        if "image" in last_user.lower():
            return "Generating a demo preview. Connect Gemini or OpenWebUI for real outputs."
        return "Demo response: provider integration is active. Configure Gemini or OpenWebUI for production output."
