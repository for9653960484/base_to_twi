"""Минимальные модели для подсчёта связей оборудования."""

from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.document import Document  # noqa: F401 — re-export

class TechCard(Base):
    __tablename__ = "tech_cards"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    equipment_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("equipment.id"))


class WorkInstruction(Base):
    __tablename__ = "work_instructions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    equipment_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("equipment.id"))


class TwiCourse(Base):
    __tablename__ = "twi_courses"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    equipment_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("equipment.id"))


class EquipmentCompetency(Base):
    __tablename__ = "equipment_competencies"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    equipment_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("equipment.id"))
