from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Recruitment Assistant"
    environment: str = "development"
    log_level: str = "INFO"

    # pydantic-settings treats List[...] env vars as JSON by default. To support
    # the documented comma-separated format in .env/.env.example, accept either
    # a string or a list and normalize to a list.
    allowed_origins: List[str] | str = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    database_url: str | None = None

    jwt_secret: str = "change-me"
    jwt_access_token_minutes: int = 30
    jwt_refresh_token_days: int = 30

    # Providers (Chunk 3)
    default_llm_provider: str = "gemini"
    default_gemini_model: str = "gemini-2.5-flash"
    gemini_api_key: str | None = None
    openwebui_base_url: str | None = None
    openwebui_api_key: str | None = None

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _split_origins(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return []
            # Allow JSON list strings too (e.g. ["http://...", "http://..."]).
            if s.startswith("["):
                try:
                    parsed = json.loads(s)
                    if isinstance(parsed, list):
                        return [str(x).strip() for x in parsed if str(x).strip()]
                except Exception:
                    pass
            return [x.strip() for x in s.split(",") if x.strip()]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()

