from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.shared.schemas import ContentStatus, MaintenanceType, TimestampMixin


class WorkItem(BaseModel):
    order: int
    description: str
    tools: list[str] = Field(default_factory=list)
    safety: list[str] = Field(default_factory=list)
    control_params: dict[str, Any] = Field(default_factory=dict)


class TechCardCreate(BaseModel):
    equipment_id: UUID
    maintenance_type: MaintenanceType
    title: str
    work_items: list[WorkItem] = Field(default_factory=list)


class TechCardResponse(TimestampMixin):
    id: UUID
    equipment_id: UUID
    maintenance_type: MaintenanceType
    title: str
    work_items: list[WorkItem]
    status: ContentStatus
