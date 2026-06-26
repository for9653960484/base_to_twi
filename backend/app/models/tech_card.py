from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

CONTENT_STATUS = ENUM(
    "draft", "pending_approval", "published", "archived",
    name="content_status", create_type=False,
)
MAINTENANCE_TYPE = ENUM(
    "annual", "semi_annual", "quarterly", "monthly", "weekly", "daily",
    name="maintenance_type", create_type=False,
)


class TechCard(Base):
    __tablename__ = "tech_cards"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    equipment_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("equipment.id", ondelete="CASCADE"), nullable=False
    )
    maintenance_type: Mapped[str] = mapped_column(MAINTENANCE_TYPE, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    work_items: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    status: Mapped[str] = mapped_column(CONTENT_STATUS, nullable=False, default="draft")
    current_version_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    source_document_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("documents.id")
    )
    custom_attributes: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
