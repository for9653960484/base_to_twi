from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.shared.schemas import ContentStatus, TimestampMixin


class StepKeyPoint(BaseModel):
    content: str
    sort_order: int = 0


class StepReason(BaseModel):
    content: str
    sort_order: int = 0


class StepMedia(BaseModel):
    file_path: str
    media_type: str = "image"
    caption: Optional[str] = None
    sort_order: int = 0


class InstructionStep(BaseModel):
    step_number: int
    title: str
    description: Optional[str] = None
    safety_notes: Optional[str] = None
    tools: list[str] = Field(default_factory=list)
    consumables: list[str] = Field(default_factory=list)
    control_params: dict[str, Any] = Field(default_factory=dict)
    key_points: list[StepKeyPoint] = Field(default_factory=list)
    reasons: list[StepReason] = Field(default_factory=list)
    media: list[StepMedia] = Field(default_factory=list)


class InstructionCreate(BaseModel):
    equipment_id: UUID
    tech_card_id: Optional[UUID] = None
    title: str
    purpose: Optional[str] = None
    scope: Optional[str] = None


class InstructionResponse(TimestampMixin):
    id: UUID
    equipment_id: UUID
    tech_card_id: Optional[UUID] = None
    title: str
    purpose: Optional[str] = None
    scope: Optional[str] = None
    status: ContentStatus
    steps: list[InstructionStep] = Field(default_factory=list)


class InstructionStepsUpdate(BaseModel):
    steps: list[InstructionStep]


class AIGenerateRequest(BaseModel):
    source_document_id: Optional[UUID] = None
    tech_card_id: Optional[UUID] = None
