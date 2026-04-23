from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import SchemaVersionTemplate


class ResumeTemplateInfo(BaseModel):
    template_id: str = Field(min_length=1, max_length=60)
    display_name: str = Field(min_length=1, max_length=80)
    supported_sections: list[str] = Field(default_factory=list)


TemplateVisibilityMode = Literal["auto", "always", "never"]


class TemplateVisibility(BaseModel):
    mode: TemplateVisibilityMode = "auto"
    min_items: int | None = Field(default=None, ge=1, description="If set, requires at least N items")


class TemplateSort(BaseModel):
    by: str = Field(min_length=1, max_length=80)
    direction: Literal["asc", "desc"] = "desc"


class TemplateLimits(BaseModel):
    max_items: int | None = Field(default=None, ge=1)
    max_bullets_per_item: int | None = Field(default=None, ge=0)


class TemplateBlockText(BaseModel):
    kind: Literal["text"] = "text"
    source: str | None = Field(default=None, description="Relative field path (e.g., 'summary.about')")
    template: str | None = Field(default=None, description="String template with {path} placeholders")
    fallback_template: str | None = None
    fallback_if_missing: list[str] = Field(default_factory=list)


class TemplateBlockBullets(BaseModel):
    kind: Literal["bullets"] = "bullets"
    source: str = Field(min_length=1, max_length=120)


class TemplateBlockTags(BaseModel):
    kind: Literal["tags"] = "tags"
    source: str = Field(min_length=1, max_length=120)
    item_path: str | None = Field(default=None, description="If list items are objects, extract this field")


class TemplateBlockLinks(BaseModel):
    kind: Literal["links"] = "links"
    source: str = Field(default="links", min_length=1, max_length=120)


class TemplateBlockTimeline(BaseModel):
    kind: Literal["timeline"] = "timeline"
    source: str = Field(min_length=1, max_length=120)

    heading_template: str = Field(min_length=1, max_length=240)

    subheading_path: str | None = None
    subheading_template: str | None = None
    subheading_fallback_template: str | None = None
    subheading_fallback_if_missing: list[str] = Field(default_factory=list)

    start_path: str | None = None
    end_path: str | None = None
    is_current_path: str | None = None
    end_current_value: str = "Present"
    bullets_path: str | None = None

    sort: TemplateSort | None = None
    limits: TemplateLimits | None = None


class TemplateBlockSkillGroupLines(BaseModel):
    kind: Literal["skill_group_lines"] = "skill_group_lines"
    source: str = Field(default="skills", min_length=1, max_length=120)


class TemplateBlockBulletsFromItems(BaseModel):
    kind: Literal["bullets_from_items"] = "bullets_from_items"
    source: str = Field(min_length=1, max_length=120)
    item_template: str = Field(min_length=1, max_length=240)
    fallback_template: str | None = None
    fallback_if_missing: list[str] = Field(default_factory=list)
    sort: TemplateSort | None = None
    limits: TemplateLimits | None = None


TemplateBlockSpec = Annotated[
    Union[
        TemplateBlockText,
        TemplateBlockBullets,
        TemplateBlockTags,
        TemplateBlockLinks,
        TemplateBlockTimeline,
        TemplateBlockSkillGroupLines,
        TemplateBlockBulletsFromItems,
    ],
    Field(discriminator="kind"),
]


class TemplateSectionSpec(BaseModel):
    section_key: str = Field(
        min_length=1,
        max_length=120,
        description="e.g., 'experience', 'skills', 'custom_sections', or 'custom:<section_id>'",
    )
    title: str | None = Field(default=None, max_length=80)
    visibility: TemplateVisibility = Field(default_factory=TemplateVisibility)
    blocks: list[TemplateBlockSpec] = Field(default_factory=list)

    @field_validator("section_key")
    @classmethod
    def _validate_section_key(cls, v: str) -> str:
        allowed = {
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
            "custom_sections",
        }
        if v in allowed:
            return v
        if v.startswith("custom:") and v.split(":", 1)[1].strip():
            return v
        raise ValueError("Unsupported section_key")


def _validate_tw_classes_map(value: dict[str, str] | None) -> dict[str, str] | None:
    if value is None:
        return None
    for k, v in value.items():
        if not isinstance(k, str) or not isinstance(v, str):
            raise ValueError("theme_classes keys and values must be strings")
        if len(k) > 80 or len(v) > 400:
            raise ValueError("theme_classes entries are too long")
        # Strict-ish allowlist to reduce injection risk (disallows brackets/quotes).
        import re

        if not re.fullmatch(r"[A-Za-z0-9:\-_/\s.]+", v):
            raise ValueError("theme_classes contains unsupported characters")
    return value


class ResumeTemplateDefinition(BaseModel):
    template_schema_version: SchemaVersionTemplate = "resume_template.v1"

    template_id: str = Field(min_length=1, max_length=60)
    template_version: str = Field(min_length=1, max_length=40)
    display_name: str = Field(min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=400)

    is_published: bool = True
    published_at: datetime | None = None

    theme_classes: dict[str, str] | None = None
    layout: dict[str, object] | None = None
    sections: list[TemplateSectionSpec] = Field(default_factory=list)

    @field_validator("theme_classes")
    @classmethod
    def _validate_theme_classes(cls, v):
        return _validate_tw_classes_map(v)


class TemplateSummary(BaseModel):
    template_id: str
    template_version: str
    display_name: str
    description: str | None = None
    is_published: bool
    published_at: datetime | None = None
    theme_classes: dict[str, str] | None = None
    layout: dict[str, object] | None = None
    section_specs: list[TemplateSectionSpec] = Field(default_factory=list)


class TemplateResolveResult(BaseModel):
    template: ResumeTemplateDefinition
    used_latest: bool = False

