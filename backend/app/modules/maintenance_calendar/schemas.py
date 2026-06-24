from datetime import date
from uuid import UUID

from pydantic import BaseModel

from app.shared.schemas import MaintenanceType


class CalendarEntry(BaseModel):
    id: UUID
    equipment_id: UUID
    equipment_name: str
    tech_card_id: UUID
    scheduled_date: date
    maintenance_type: MaintenanceType
    title: str
    is_completed: bool


class CalendarGenerateRequest(BaseModel):
    equipment_id: UUID | None = None
    from_date: date
    to_date: date
