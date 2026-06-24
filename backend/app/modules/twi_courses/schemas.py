from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.shared.schemas import ContentStatus, TimestampMixin


class CourseContent(BaseModel):
    preparation: Optional[str] = None
    typical_mistakes: list[str] = Field(default_factory=list)
    self_check_questions: list[str] = Field(default_factory=list)
    reinforcement_tips: list[str] = Field(default_factory=list)
    slides: list[dict[str, Any]] = Field(default_factory=list)


class CourseCreate(BaseModel):
    instruction_id: UUID
    title: str


class CourseResponse(TimestampMixin):
    id: UUID
    instruction_id: UUID
    equipment_id: UUID
    title: str
    content: CourseContent
    status: ContentStatus


class CourseAssignRequest(BaseModel):
    user_ids: list[UUID]


class CourseAssignmentResponse(BaseModel):
    id: UUID
    course_id: UUID
    user_id: UUID
    user_name: str
    status: str
    assigned_at: datetime
    completed_at: Optional[datetime] = None
