from __future__ import annotations

from datetime import date
from typing import Annotated, Generic, Literal, TypeVar

from pydantic import BaseModel, Field, HttpUrl


SchemaVersionCandidate = Literal["candidate_profile.v1"]
SchemaVersionResume = Literal["resume_document.v1", "resume_document.v2"]

SchemaVersionTemplate = Literal["resume_template.v1"]

ISODate = Annotated[date, Field(description="ISO-8601 date")]
URL = Annotated[HttpUrl, Field(description="URL")]


class APIError(BaseModel):
    error: str
    detail: object | None = None
    request_id: str | None = None


class APIMeta(BaseModel):
    request_id: str | None = None
    provider: str | None = None
    model: str | None = None
    warnings: list[str] = Field(default_factory=list)


PayloadT = TypeVar("PayloadT")


class APIResponse(BaseModel, Generic[PayloadT]):
    ok: bool = True
    data: PayloadT
    meta: APIMeta | None = None
