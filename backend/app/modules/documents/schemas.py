from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.shared.schemas import AIProcessingStatus, ContentStatus, CustomAttributesMixin, TimestampMixin


class DocumentUploadResponse(CustomAttributesMixin, TimestampMixin):
    id: UUID
    equipment_id: UUID
    equipment_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    file_path: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    status: ContentStatus
    ai_processing_status: AIProcessingStatus
    current_version_number: Optional[int] = None


class DocumentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    equipment_id: Optional[UUID] = None
    custom_attributes: Optional[dict[str, Any]] = None


class DocumentVersionResponse(BaseModel):
    id: UUID
    version_number: int
    status: ContentStatus
    change_summary: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    created_at: datetime


class AIProcessRequest(BaseModel):
    force_reprocess: bool = False


class AIStatusResponse(BaseModel):
    document_id: UUID
    ai_processing_status: AIProcessingStatus
    task_id: Optional[UUID] = None
    celery_task_id: Optional[str] = None
    progress: Optional[int] = None
    result_summary: Optional[str] = None
    error_message: Optional[str] = None
    maintenance_works_count: Optional[int] = None


class DocumentUploadVersionRequest(BaseModel):
    change_summary: Optional[str] = None
