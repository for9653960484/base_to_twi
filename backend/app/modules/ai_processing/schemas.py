from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel


class AITaskCreate(BaseModel):
    task_type: str
    equipment_id: Optional[UUID] = None
    source_type: Optional[str] = None
    source_id: Optional[UUID] = None
    input_payload: dict[str, Any] = {}


class AITaskResponse(BaseModel):
    id: UUID
    task_type: str
    status: str
    celery_task_id: Optional[str] = None
    result_payload: Optional[dict[str, Any]] = None
    error_message: Optional[str] = None


class AICallbackPayload(BaseModel):
    task_id: UUID
    status: str
    source_type: Optional[str] = None
    source_id: Optional[UUID] = None
    document_ai_status: Optional[str] = None
    result_payload: Optional[dict[str, Any]] = None
    error_message: Optional[str] = None
