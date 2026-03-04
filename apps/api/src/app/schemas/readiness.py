"""Readiness score schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ReadinessItem(BaseModel):
    """Readiness score and breakdown for a grid cell."""

    cell_id: str
    score: float = Field(ge=0, le=100)
    breakdown: dict[str, Any]
    updated_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cell_id": "mock-cell-001",
                "score": 72.5,
                "breakdown": {
                    "baseline_vulnerability": 0.3,
                    "recent_hazards": 0.4,
                    "accessibility": 0.2,
                    "coverage_confidence": 0.1,
                },
                "updated_at": "2026-02-25T09:46:30Z",
            }
        }
    )


class ReadinessListResponse(BaseModel):
    """Collection of readiness score items."""

    items: list[ReadinessItem]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "cell_id": "mock-cell-001",
                        "score": 72.5,
                        "breakdown": {
                            "baseline_vulnerability": 0.3,
                            "recent_hazards": 0.4,
                            "accessibility": 0.2,
                            "coverage_confidence": 0.1,
                        },
                        "updated_at": "2026-02-25T09:46:30Z",
                    }
                ]
            }
        }
    )
