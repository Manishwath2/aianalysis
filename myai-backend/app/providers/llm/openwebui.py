from __future__ import annotations

import httpx

from app.core.config import get_settings
from app.providers.llm.base import LLMProviderAdapter, ProviderConfigError, ProviderRequestError
from app.schemas.chat import ChatCompletionMessage
from app.schemas.llm import LLMModel


class OpenWebUIProvider(LLMProviderAdapter):
    provider_name = "openwebui"

    def __init__(self) -> None:
        self.settings = get_settings()

    def is_configured(self) -> bool:
        return bool(self.settings.openwebui_base_url)

    def default_model(self) -> str:
        return "openwebui/default"

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.settings.openwebui_api_key:
            headers["Authorization"] = f"Bearer {self.settings.openwebui_api_key}"
        return headers

    async def list_models(self) -> list[LLMModel]:
        if not self.is_configured():
            return []

        url = f"{self.settings.openwebui_base_url.rstrip('/')}/api/models"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, headers=self._headers())
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            raise ProviderRequestError("Failed to list OpenWebUI models") from exc

        raw_models = data.get("data") or data.get("models") or []
        out: list[LLMModel] = []
        for m in raw_models:
            model_id = m.get("id") or m.get("name")
            if not model_id:
                continue
            out.append(LLMModel(id=model_id, provider="openwebui", display_name=m.get("name") or model_id))
        return out

    async def complete_chat(self, *, messages: list[ChatCompletionMessage], model: str | None) -> str:
        if not self.is_configured():
            raise ProviderConfigError("OPENWEBUI_BASE_URL is not configured")

        payload = {
            "model": model or "openwebui/default",
            "messages": [m.model_dump() for m in messages],
            "stream": False,
        }
        url = f"{self.settings.openwebui_base_url.rstrip('/')}/api/chat/completions"

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                resp = await client.post(url, headers=self._headers(), json=payload)
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            raise ProviderRequestError("OpenWebUI chat completion failed") from exc

        choices = data.get("choices") or []
        if not choices:
            return ""
        return (choices[0].get("message", {}) or {}).get("content", "")
