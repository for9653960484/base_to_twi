from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.shared.schemas import AIProcessingStatus, ContentStatus


class PpeItem(BaseModel):
    name: str
    purpose: str = ""
    mandatory: bool = True


class ConditionItem(BaseModel):
    name: str
    value: str


class WorkConditions(BaseModel):
    temperature: str = ""
    humidity: str = ""
    voltage: str = ""
    other: list[ConditionItem] = Field(default_factory=list)


class SafetySheetResponse(BaseModel):
    id: UUID
    equipment_id: UUID
    equipment_name: Optional[str] = None
    source_document_id: Optional[UUID] = None
    title: str
    ppe: list[PpeItem] = Field(default_factory=list)
    work_conditions: WorkConditions = Field(default_factory=WorkConditions)
    notes: Optional[str] = None
    status: ContentStatus
    created_at: datetime
    updated_at: datetime


class SafetySheetUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    equipment_id: Optional[UUID] = None
    ppe: Optional[list[PpeItem]] = None
    work_conditions: Optional[WorkConditions] = None
    notes: Optional[str] = None


class SafetyGenerateRequest(BaseModel):
    document_id: UUID


class SafetyGenerateStatus(BaseModel):
    document_id: UUID
    ai_processing_status: AIProcessingStatus
    task_id: Optional[UUID] = None
    celery_task_id: Optional[str] = None
    error_message: Optional[str] = None
    sheets_count: Optional[int] = None
