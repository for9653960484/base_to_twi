from uuid import UUID, uuid4

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[dict] = mapped_column(JSONB, nullable=False)
    permissions: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    external_id: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    specialization_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    department_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    custom_attributes: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
