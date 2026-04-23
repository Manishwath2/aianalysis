"""create resume templates

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-22
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def upgrade() -> None:
    op.create_table(
        "resume_template_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("template_id", sa.String(length=60), nullable=False),
        sa.Column("template_version", sa.String(length=40), nullable=False),
        sa.Column("template_schema_version", sa.String(length=40), nullable=False),
        sa.Column("display_name", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("definition", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("template_id", "template_version", name="uq_template_id_version"),
    )
    op.create_index("ix_template_id", "resume_template_versions", ["template_id"], unique=False)
    op.create_index(
        "ix_template_id_version",
        "resume_template_versions",
        ["template_id", "template_version"],
        unique=True,
    )

    templates = sa.table(
        "resume_template_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True)),
        sa.Column("template_id", sa.String(length=60)),
        sa.Column("template_version", sa.String(length=40)),
        sa.Column("template_schema_version", sa.String(length=40)),
        sa.Column("display_name", sa.String(length=80)),
        sa.Column("description", sa.Text()),
        sa.Column("is_published", sa.Boolean()),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("definition", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    # Minimal initial templates; mapping logic is interpreted by the backend engine.
    classic_def = {
        "template_schema_version": "resume_template.v1",
        "template_id": "classic",
        "template_version": "1.0.0",
        "display_name": "Classic",
        "description": "Single-column classic resume.",
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
                        "template": "{personal.full_name} — {personal.headline}",
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
                        "heading_template": "{role} • {company}",
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
                        "subheading_template": "{degree} — {field_of_study}",
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

    modern_def = {
        **classic_def,
        "template_id": "modern",
        "template_version": "1.0.0",
        "display_name": "Modern",
        "description": "Modern ordering with experience earlier.",
        "sections": [
            classic_def["sections"][0],
            classic_def["sections"][1],
            classic_def["sections"][3],
            classic_def["sections"][2],
            classic_def["sections"][4],
            classic_def["sections"][5],
            classic_def["sections"][6],
            classic_def["sections"][7],
            classic_def["sections"][8],
        ],
    }

    compact_def = {
        **classic_def,
        "template_id": "compact",
        "template_version": "1.0.0",
        "display_name": "Compact",
        "description": "Compact resume with fewer sections.",
        "sections": [
            classic_def["sections"][0],
            classic_def["sections"][1],
            classic_def["sections"][2],
            classic_def["sections"][3],
            classic_def["sections"][5],
            classic_def["sections"][7],
        ],
    }

    now = _now()
    op.bulk_insert(
        templates,
        [
            {
                "id": uuid.uuid4(),
                "template_id": "classic",
                "template_version": "1.0.0",
                "template_schema_version": "resume_template.v1",
                "display_name": "Classic",
                "description": "Single-column classic resume.",
                "is_published": True,
                "published_at": now,
                "definition": classic_def,
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": uuid.uuid4(),
                "template_id": "modern",
                "template_version": "1.0.0",
                "template_schema_version": "resume_template.v1",
                "display_name": "Modern",
                "description": "Modern ordering with experience earlier.",
                "is_published": True,
                "published_at": now,
                "definition": modern_def,
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": uuid.uuid4(),
                "template_id": "compact",
                "template_version": "1.0.0",
                "template_schema_version": "resume_template.v1",
                "display_name": "Compact",
                "description": "Compact resume with fewer sections.",
                "is_published": True,
                "published_at": now,
                "definition": compact_def,
                "created_at": now,
                "updated_at": now,
            },
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_template_id_version", table_name="resume_template_versions")
    op.drop_index("ix_template_id", table_name="resume_template_versions")
    op.drop_table("resume_template_versions")
