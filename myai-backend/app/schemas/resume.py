from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, Union
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl

from app.schemas.common import SchemaVersionResume


SectionType = Literal[
    "header",
    "summary",
    "skills",
    "experience",
    "education",
    "projects",
    "certifications",
    "links",
    "achievements",
    "languages",
    "custom",
]


class RenderHints(BaseModel):
    section_order: list[SectionType] | None = None
    emphasis: dict[str, str] | None = None


class ResumeWarning(BaseModel):
    code: str
    message: str
    section_key: str | None = None


class TextBlock(BaseModel):
    type: Literal["text"] = "text"
    text: str


class BulletsBlock(BaseModel):
    type: Literal["bullets"] = "bullets"
    items: list[str]


class TagBlock(BaseModel):
    type: Literal["tags"] = "tags"
    items: list[str]


class LinkBlock(BaseModel):
    type: Literal["link"] = "link"
    label: str
    url: HttpUrl


class TimelineItem(BaseModel):
    heading: str
    subheading: str | None = None
    start: str | None = None
    end: str | None = None
    bullets: list[str] = Field(default_factory=list)


class TimelineBlock(BaseModel):
    type: Literal["timeline"] = "timeline"
    items: list[TimelineItem]


ResumeBlock = Annotated[Union[TextBlock, BulletsBlock, TagBlock, LinkBlock, TimelineBlock], Field(discriminator="type")]


class ResumeSection(BaseModel):
    type: SectionType
    key: str | None = None
    title: str | None = None
    blocks: list[ResumeBlock] = Field(default_factory=list)


class ResumeDocument(BaseModel):
    schema_version: SchemaVersionResume = "resume_document.v1"
    resume_id: UUID
    candidate_id: UUID
    template_id: str = Field(min_length=1, max_length=60)
    template_version: str | None = Field(default=None, max_length=40)
    locale: str = Field(default="en-US", max_length=20)
    created_at: datetime
    render_hints: RenderHints | None = None
    sections: list[ResumeSection]

