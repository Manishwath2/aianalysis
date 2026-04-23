from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ResumeTemplateVersion(Base):
    __tablename__ = "resume_template_versions"
    __table_args__ = (
        UniqueConstraint("template_id", "template_version", name="uq_template_id_version"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    template_id: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    template_version: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    template_schema_version: Mapped[str] = mapped_column(String(40), nullable=False, default="resume_template.v1")

    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    definition: Mapped[dict] = mapped_column(JSONB, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
