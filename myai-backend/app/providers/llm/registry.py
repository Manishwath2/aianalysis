from __future__ import annotations

from app.core.config import get_settings
from app.providers.llm.base import LLMProviderAdapter
from app.providers.llm.demo import DemoProvider
from app.providers.llm.gemini import GeminiProvider
from app.providers.llm.openwebui import OpenWebUIProvider
from app.schemas.llm import LLMProviderHealth, LLMProviderInfo


class ProviderRegistry:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._providers: dict[str, LLMProviderAdapter] = {
            "gemini": GeminiProvider(),
            "openwebui": OpenWebUIProvider(),
            "demo": DemoProvider(),
        }

    def get(self, name: str | None) -> LLMProviderAdapter:
        if name and name in self._providers:
            selected = self._providers[name]
            if selected.is_configured() or name == "demo":
                return selected

        for preferred in (self.settings.default_llm_provider, "gemini", "openwebui"):
            if preferred not in self._providers:
                continue
            p = self._providers[preferred]
            if p.is_configured():
                return p

        return self._providers["demo"]

    def list_infos(self) -> list[LLMProviderInfo]:
        out: list[LLMProviderInfo] = []
        for key, provider in self._providers.items():
            configured = provider.is_configured()
            out.append(
                LLMProviderInfo(
                    provider=key,
                    display_name=("Google Gemini" if key == "gemini" else "OpenWebUI Gateway" if key == "openwebui" else "Demo"),
                    status="available" if configured or key == "demo" else "planned",
                )
            )
        return out

    def health(self) -> list[LLMProviderHealth]:
        out: list[LLMProviderHealth] = []
        for key, provider in self._providers.items():
            status = "available" if provider.is_configured() or key == "demo" else "down"
            out.append(LLMProviderHealth(provider=key, status=status, detail=None))
        return out


registry = ProviderRegistry()
