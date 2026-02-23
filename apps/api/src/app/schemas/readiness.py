"""Readiness score schemas (skeleton)."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ReadinessItem(BaseModel):
    """Readiness score and breakdown for a grid cell."""

    cell_id: str
    score: float = Field(ge=0, le=100)
    breakdown: dict[str, Any]
    updated_at: datetime


class ReadinessListResponse(BaseModel):
    """Collection of readiness score items."""

    items: list[ReadinessItem]
