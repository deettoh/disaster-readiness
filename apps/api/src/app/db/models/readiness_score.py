"""ORM model for readiness scores."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base


class ReadinessScore(Base):
    """ORM model for public.readiness_scores."""

    __tablename__ = "readiness_scores"
    __table_args__ = {"schema": "public"}

    cell_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("public.grid_cells.id"),
        primary_key=True,
    )
    score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    breakdown: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

