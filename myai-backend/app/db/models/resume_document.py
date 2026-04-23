from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ResumeDocumentRecord(Base):
    __tablename__ = "resume_documents"

    resume_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True, nullable=False)
    template_id: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    template_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    locale: Mapped[str] = mapped_column(String(20), nullable=False, default="en-US")
    document: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
