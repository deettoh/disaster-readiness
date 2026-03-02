"""SQLAlchemy ORM models for API data access."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from geoalchemy2 import Geography
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base declarative class for API ORM models."""


class Report(Base):
    """ORM model for public.reports."""

    __tablename__ = "reports"
    __table_args__ = {"schema": "public"}

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    geom: Mapped[Any | None] = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=True,
    )
    hazard_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    source: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    images: Mapped[list[Image]] = relationship(back_populates="report")


class Image(Base):
    """ORM model for public.images."""

    __tablename__ = "images"
    __table_args__ = {"schema": "public"}

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    report_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("public.reports.id"),
        nullable=True,
    )
    bucket_path: Mapped[str] = mapped_column(Text, nullable=False)
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    report: Mapped[Report | None] = relationship(back_populates="images")


class GridCell(Base):
    """ORM model for public.grid_cells."""

    __tablename__ = "grid_cells"
    __table_args__ = {"schema": "public"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cell_id: Mapped[str | None] = mapped_column(Text, nullable=True)


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


class Alert(Base):
    """ORM model for public.alerts."""

    __tablename__ = "alerts"
    __table_args__ = {"schema": "public"}

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    cell_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("public.grid_cells.id"),
        nullable=True,
    )
    severity: Mapped[str | None] = mapped_column(Text, nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
