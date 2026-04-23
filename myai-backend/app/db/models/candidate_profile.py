from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CandidateProfileRecord(Base):
    __tablename__ = "candidate_profiles"

    candidate_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    headline: Mapped[str | None] = mapped_column(String(180), nullable=True)
    location: Mapped[str | None] = mapped_column(String(120), nullable=True)
    source: Mapped[str | None] = mapped_column(String(80), nullable=True)
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
