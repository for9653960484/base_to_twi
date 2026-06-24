from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

AI_TASK_TYPE = ENUM(
    "document_parse", "extract_maintenance", "generate_instruction",
    "generate_course", "generate_competencies", "qa_search", "reindex",
    name="ai_task_type", create_type=False,
)
AI_TASK_STATUS = ENUM(
    "pending", "processing", "completed", "failed", "cancelled",
    name="ai_task_status", create_type=False,
)


class AITask(Base):
    __tablename__ = "ai_tasks"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    task_type: Mapped[str] = mapped_column(AI_TASK_TYPE, nullable=False)
    status: Mapped[str] = mapped_column(AI_TASK_STATUS, nullable=False, default="pending")
    equipment_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("equipment.id"))
    source_type: Mapped[str | None] = mapped_column(String(50))
    source_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    input_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    result_payload: Mapped[dict | None] = mapped_column(JSONB)
    error_message: Mapped[str | None] = mapped_column(Text)
    celery_task_id: Mapped[str | None] = mapped_column(String(255))
    created_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
