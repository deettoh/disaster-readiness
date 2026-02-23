"""Alert schemas (scaffold)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AlertItem(BaseModel):
    alert_id: UUID
    level: str
    message: str
    cell_id: str
    created_at: datetime


class AlertListResponse(BaseModel):
    items: list[AlertItem]

