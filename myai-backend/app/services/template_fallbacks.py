from __future__ import annotations

from datetime import datetime

from app.schemas.templates import ResumeTemplateDefinition


def _now() -> datetime:
    return datetime.utcnow()


def _classic_def() -> dict[str, object]:
    return {
        "template_schema_version": "resume_template.v1",
        "template_id": "classic",
        "template_version": "1.0.0",
        "display_name": "Classic",
        "description": "Single-column classic resume.",
        "is_published": True,
        "published_at": _now(),
        "theme_classes": {
            "page": "bg-white text-zinc-900",
            "section_title": "text-sm font-semibold tracking-wide uppercase",
            "text": "text-sm",
            "muted": "text-zinc-600",
        },
        "layout": {"page": "max-w-[850px] mx-auto", "columns": 1},
        "sections": [
            {
                "section_key": "header",
                "title": None,
                "visibility": {"mode": "always"},
                "blocks": [
                    {
                        "kind": "text",
                        "template": "{personal.full_name} - {personal.headline}",
                        "fallback_template": "{personal.full_name}",
                        "fallback_if_missing": ["personal.headline"],
                    }
                ],
            },
            {
                "section_key": "summary",
                "title": "Summary",
                "visibility": {"mode": "auto"},
                "blocks": [
                    {"kind": "text", "source": "summary.about"},
                    {"kind": "bullets", "source": "summary.highlights"},
                ],
            },
            {
                "section_key": "skills",
                "title": "Skills",
                "visibility": {"mode": "auto"},
                "blocks": [{"kind": "skill_group_lines", "source": "skills"}],
            },
            {
                "section_key": "experience",
                "title": "Experience",
                "visibility": {"mode": "auto"},
                "blocks": [
                    {
                        "kind": "timeline",
                        "source": "experience",
                        "heading_template": "{role} | {company}",
                        "subheading_path": "location",
                        "start_path": "date_range.start",
                        "end_path": "date_range.end",
                        "is_current_path": "date_range.is_current",
                        "end_current_value": "Present",
                        "bullets_path": "bullets",
                        "sort": {"by": "date_range.start", "direction": "desc"},
                        "limits": {"max_items": 10, "max_bullets_per_item": 6},
                    }
                ],
            },
            {
                "section_key": "projects",
                "title": "Projects",
                "visibility": {"mode": "auto"},
                "blocks": [
                    {
                        "kind": "bullets_from_items",
                        "source": "projects",
                        "item_template": "{name}: {description}",
                        "fallback_template": "{name}",
                        "fallback_if_missing": ["description"],
                        "limits": {"max_items": 8},
                    }
                ],
            },
            {
                "section_key": "education",
                "title": "Education",
                "visibility": {"mode": "auto"},
                "blocks": [
                    {
                        "kind": "timeline",
                        "source": "education",
                        "heading_template": "{school}",
                        "subheading_template": "{degree} - {field_of_study}",
                        "subheading_fallback_template": "{degree}",
                        "subheading_fallback_if_missing": ["field_of_study"],
                        "start_path": "date_range.start",
                        "end_path": "date_range.end",
                        "bullets_path": "highlights",
                        "sort": {"by": "date_range.start", "direction": "desc"},
                        "limits": {"max_items": 5, "max_bullets_per_item": 4},
                    }
                ],
            },
            {
                "section_key": "certifications",
                "title": "Certifications",
                "visibility": {"mode": "auto"},
                "blocks": [{"kind": "tags", "source": "certifications", "item_path": "name"}],
            },
            {
                "section_key": "links",
                "title": "Links",
                "visibility": {"mode": "auto"},
                "blocks": [{"kind": "links", "source": "links"}],
            },
            {
                "section_key": "custom_sections",
                "title": None,
                "visibility": {"mode": "auto"},
                "blocks": [],
            },
        ],
    }


def _modern_def(classic: dict[str, object]) -> dict[str, object]:
    sections = classic["sections"]
    return {
        **classic,
        "template_id": "modern",
        "template_version": "1.0.0",
        "display_name": "Modern",
        "description": "Modern ordering with experience earlier.",
        "sections": [
            sections[0],
            sections[1],
            sections[3],
            sections[2],
            sections[4],
            sections[5],
            sections[6],
            sections[7],
            sections[8],
        ],
    }


def _compact_def(classic: dict[str, object]) -> dict[str, object]:
    sections = classic["sections"]
    return {
        **classic,
        "template_id": "compact",
        "template_version": "1.0.0",
        "display_name": "Compact",
        "description": "Compact resume with fewer sections.",
        "sections": [
            sections[0],
            sections[1],
            sections[2],
            sections[3],
            sections[5],
            sections[7],
        ],
    }


def fallback_templates() -> list[ResumeTemplateDefinition]:
    classic = _classic_def()
    modern = _modern_def(classic)
    compact = _compact_def(classic)
    return [
        ResumeTemplateDefinition.model_validate(classic),
        ResumeTemplateDefinition.model_validate(modern),
        ResumeTemplateDefinition.model_validate(compact),
    ]
