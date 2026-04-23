from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, HttpUrl

from app.schemas.common import SchemaVersionCandidate


DateString = Annotated[
    str,
    Field(
        description="Date string (YYYY, YYYY-MM, or YYYY-MM-DD).",
        pattern=r"^\d{4}(-\d{2})?(-\d{2})?$",
        examples=["2022", "2022-05", "2022-05-01"],
    ),
]


class Meta(BaseModel):
    created_at: datetime | None = None
    updated_at: datetime | None = None
    tags: list[str] = Field(default_factory=list, description="Free-form tags (e.g., 'frontend', 'python').")
    source: str | None = Field(default=None, max_length=80, description="Where the profile came from.")
    extra: dict[str, object] = Field(
        default_factory=dict,
        description="Extension bag for future fields without breaking the schema.",
    )


class PersonalInfo(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)
    headline: str | None = Field(default=None, max_length=180)
    location: str | None = Field(default=None, max_length=120)
    pronouns: str | None = Field(default=None, max_length=40)


class ContactInfo(BaseModel):
    emails: list[EmailStr] = Field(default_factory=list)
    phones: list[str] = Field(default_factory=list, description="E.164 recommended.")
    address: str | None = Field(default=None, max_length=240)


class LinkItem(BaseModel):
    kind: Literal[
        "website",
        "linkedin",
        "github",
        "portfolio",
        "twitter",
        "medium",
        "devto",
        "other",
    ] = "other"
    label: str = Field(min_length=1, max_length=60)
    url: HttpUrl


class SummarySection(BaseModel):
    about: str | None = Field(default=None, max_length=2400)
    highlights: list[str] = Field(
        default_factory=list,
        description="Short bullet highlights used by some templates.",
    )


class SkillItem(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    level: Literal["beginner", "intermediate", "advanced", "expert"] | None = None
    years: float | None = Field(default=None, ge=0, le=50)
    keywords: list[str] = Field(default_factory=list)


class SkillGroup(BaseModel):
    category: str = Field(min_length=1, max_length=60)
    items: list[SkillItem] = Field(default_factory=list)


class DateRange(BaseModel):
    start: DateString | None = None
    end: DateString | None = None
    is_current: bool = False


class ExperienceItem(BaseModel):
    id: str = Field(min_length=1, max_length=80, description="Stable identifier for frontend lists.")
    company: str = Field(min_length=1, max_length=120)
    role: str = Field(min_length=1, max_length=120)
    location: str | None = Field(default=None, max_length=120)
    date_range: DateRange | None = None
    summary: str | None = Field(default=None, max_length=2000)
    bullets: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)


class EducationItem(BaseModel):
    id: str = Field(min_length=1, max_length=80)
    school: str = Field(min_length=1, max_length=160)
    degree: str | None = Field(default=None, max_length=160)
    field_of_study: str | None = Field(default=None, max_length=160)
    date_range: DateRange | None = None
    grade: str | None = Field(default=None, max_length=60)
    highlights: list[str] = Field(default_factory=list)


class ProjectItem(BaseModel):
    id: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2400)
    date_range: DateRange | None = None
    links: list[HttpUrl] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    bullets: list[str] = Field(default_factory=list)


class CertificationItem(BaseModel):
    id: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=160)
    issuer: str | None = Field(default=None, max_length=160)
    issued_date: DateString | None = None
    expires_date: DateString | None = None
    credential_url: HttpUrl | None = None


class AchievementItem(BaseModel):
    id: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=1200)
    date: DateString | None = None


class LanguageItem(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    proficiency: Literal[
        "native",
        "fluent",
        "professional",
        "conversational",
        "basic",
    ] | None = None


class CustomSectionText(BaseModel):
    type: Literal["text"] = "text"
    text: str = Field(min_length=1, max_length=4000)


class CustomSectionBullets(BaseModel):
    type: Literal["bullets"] = "bullets"
    items: list[str] = Field(default_factory=list)


class CustomTimelineItem(BaseModel):
    heading: str = Field(min_length=1, max_length=200)
    subheading: str | None = Field(default=None, max_length=200)
    date_range: DateRange | None = None
    bullets: list[str] = Field(default_factory=list)


class CustomSectionTimeline(BaseModel):
    type: Literal["timeline"] = "timeline"
    items: list[CustomTimelineItem] = Field(default_factory=list)


CustomSectionBlock = Annotated[
    CustomSectionText | CustomSectionBullets | CustomSectionTimeline,
    Field(discriminator="type"),
]


class CustomSection(BaseModel):
    section_id: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=80)
    blocks: list[CustomSectionBlock] = Field(default_factory=list)


class CandidateProfile(BaseModel):
    """Master candidate profile schema for resume generation.

    Required fields are intentionally minimal to support partial profiles.
    Resume generation should degrade gracefully when optional fields are missing.
    """

    schema_version: SchemaVersionCandidate = "candidate_profile.v1"
    candidate_id: UUID
    meta: Meta | None = None

    personal: PersonalInfo
    contact: ContactInfo | None = None
    links: list[LinkItem] = Field(default_factory=list)
    summary: SummarySection | None = None

    skills: list[SkillGroup] = Field(default_factory=list)
    education: list[EducationItem] = Field(default_factory=list)
    experience: list[ExperienceItem] = Field(default_factory=list)
    projects: list[ProjectItem] = Field(default_factory=list)

    certifications: list[CertificationItem] = Field(default_factory=list)
    achievements: list[AchievementItem] = Field(default_factory=list)
    languages: list[LanguageItem] = Field(default_factory=list)

    custom_sections: list[CustomSection] = Field(default_factory=list)
