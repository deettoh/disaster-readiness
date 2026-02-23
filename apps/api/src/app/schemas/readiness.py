"""Readiness score schemas (skeleton)."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ReadinessItem(BaseModel):
    cell_id: str
    score: float = Field(ge=0, le=100)
    breakdown: dict[str, Any]
    updated_at: datetime


class ReadinessListResponse(BaseModel):
    items: list[ReadinessItem]
