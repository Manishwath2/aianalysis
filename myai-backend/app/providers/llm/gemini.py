from __future__ import annotations

import httpx

from app.core.config import get_settings
from app.providers.llm.base import LLMProviderAdapter, ProviderConfigError, ProviderRequestError
from app.schemas.chat import ChatCompletionMessage
from app.schemas.llm import LLMModel


class GeminiProvider(LLMProviderAdapter):
    provider_name = "gemini"

    def __init__(self) -> None:
        self.settings = get_settings()

    def is_configured(self) -> bool:
        return bool(self.settings.gemini_api_key)

    def default_model(self) -> str:
        return self.settings.default_gemini_model

    async def list_models(self) -> list[LLMModel]:
        if not self.is_configured():
            return []

        url = "https://generativelanguage.googleapis.com/v1beta/models"
        params = {"key": self.settings.gemini_api_key}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            raise ProviderRequestError("Failed to list Gemini models") from exc

        out: list[LLMModel] = []
        for item in data.get("models", []):
            name = item.get("name", "")
            if not name:
                continue
            model_id = name.split("models/")[-1]
            out.append(LLMModel(id=model_id, provider="gemini", display_name=item.get("displayName", model_id)))
        return out

    async def complete_chat(self, *, messages: list[ChatCompletionMessage], model: str | None) -> str:
        if not self.is_configured():
            raise ProviderConfigError("GEMINI_API_KEY is not configured")

        chosen = model or self.settings.default_gemini_model
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{chosen}:generateContent"
        params = {"key": self.settings.gemini_api_key}

        payload = self._build_payload(messages)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, params=params, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            raise ProviderRequestError("Gemini chat completion failed") from exc

        candidates = data.get("candidates", [])
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts", [])
        text_bits = [p.get("text", "") for p in parts if p.get("text")]
        return "\n".join(text_bits).strip()

    def _build_payload(self, messages: list[ChatCompletionMessage]) -> dict[str, object]:
        contents: list[dict[str, object]] = []
        system_parts: list[dict[str, str]] = []

        for message in messages:
            text = message.content.strip()
            if not text:
                continue

            if message.role == "system":
                system_parts.append({"text": text})
                continue

            gemini_role = "model" if message.role == "assistant" else "user"
            contents.append(
                {
                    "role": gemini_role,
                    "parts": [{"text": text}],
                }
            )

        if not contents:
            raise ProviderRequestError("At least one user or assistant message is required")

        payload: dict[str, object] = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.4,
            },
        }
        if system_parts:
            payload["systemInstruction"] = {"parts": system_parts}
        return payload
