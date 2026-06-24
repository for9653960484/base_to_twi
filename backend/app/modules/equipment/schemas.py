from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.shared.schemas import CustomAttributesMixin, TimestampMixin


class EquipmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    serial_name: Optional[str] = None
    description: Optional[str] = None
    custom_attributes: dict[str, Any] = Field(default_factory=dict)


class EquipmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    serial_name: Optional[str] = None
    description: Optional[str] = None
    custom_attributes: Optional[dict[str, Any]] = None
    is_active: Optional[bool] = None


class EquipmentResponse(CustomAttributesMixin, TimestampMixin):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    serial_name: Optional[str] = None
    description: Optional[str] = None
    is_active: bool


class EquipmentRelations(BaseModel):
    documents_count: int = 0
    tech_cards_count: int = 0
    instructions_count: int = 0
    courses_count: int = 0
    competencies_count: int = 0
