"""Alert schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AlertItem(BaseModel):
    """Single alert payload for frontend consumption."""

    alert_id: UUID
    level: str
    message: str
    cell_id: str
    created_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "alert_id": "3aeb07cc-1948-4ee0-b1c8-b3246e11f3ed",
                "level": "high",
                "message": "High flood risk detected in nearby cell",
                "cell_id": "mock-cell-001",
                "created_at": "2026-02-25T09:47:00Z",
            }
        }
    )


class AlertListResponse(BaseModel):
    """Collection of alert items."""

    items: list[AlertItem]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "alert_id": "3aeb07cc-1948-4ee0-b1c8-b3246e11f3ed",
                        "level": "high",
                        "message": "High flood risk detected in nearby cell",
                        "cell_id": "mock-cell-001",
                        "created_at": "2026-02-25T09:47:00Z",
                    }
                ]
            }
        }
    )
