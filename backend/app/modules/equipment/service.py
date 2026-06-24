import math
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.equipment import Equipment
from app.models.relations import (
    Document,
    EquipmentCompetency,
    TechCard,
    TwiCourse,
    WorkInstruction,
)
from app.modules.equipment.schemas import (
    EquipmentCreate,
    EquipmentRelations,
    EquipmentResponse,
    EquipmentUpdate,
)
from app.shared.schemas import PaginatedResponse


def _to_response(equipment: Equipment) -> EquipmentResponse:
    return EquipmentResponse(
        id=equipment.id,
        name=equipment.name,
        serial_name=equipment.serial_name,
        description=equipment.description,
        custom_attributes=equipment.custom_attributes or {},
        is_active=equipment.is_active,
        created_at=equipment.created_at,
        updated_at=equipment.updated_at,
    )


class EquipmentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> PaginatedResponse[EquipmentResponse]:
        query = select(Equipment)
        count_query = select(func.count()).select_from(Equipment)

        if search:
            pattern = f"%{search}%"
            filter_expr = or_(
                Equipment.name.ilike(pattern),
                Equipment.serial_name.ilike(pattern),
            )
            query = query.where(filter_expr)
            count_query = count_query.where(filter_expr)

        if is_active is not None:
            query = query.where(Equipment.is_active == is_active)
            count_query = count_query.where(Equipment.is_active == is_active)

        total = (await self.db.execute(count_query)).scalar_one()

        query = (
            query.order_by(Equipment.name)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(query)
        items = [_to_response(e) for e in result.scalars().all()]

        pages = math.ceil(total / page_size) if total > 0 else 0
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def get(self, equipment_id: UUID) -> EquipmentResponse:
        equipment = await self._get_or_raise(equipment_id)
        return _to_response(equipment)

    async def create(self, data: EquipmentCreate, created_by: UUID | None) -> EquipmentResponse:
        equipment = Equipment(
            name=data.name,
            serial_name=data.serial_name,
            description=data.description,
            custom_attributes=data.custom_attributes,
            created_by=created_by,
        )
        self.db.add(equipment)
        await self.db.flush()
        await self.db.refresh(equipment)
        return _to_response(equipment)

    async def update(self, equipment_id: UUID, data: EquipmentUpdate) -> EquipmentResponse:
        equipment = await self._get_or_raise(equipment_id)
        update_data = data.model_dump(exclude_unset=True)

        if "custom_attributes" in update_data and update_data["custom_attributes"] is not None:
            merged = {**(equipment.custom_attributes or {}), **update_data["custom_attributes"]}
            update_data["custom_attributes"] = merged

        for field, value in update_data.items():
            setattr(equipment, field, value)

        equipment.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(equipment)
        return _to_response(equipment)

    async def get_relations(self, equipment_id: UUID) -> EquipmentRelations:
        await self._get_or_raise(equipment_id)

        async def count(model, eid: UUID) -> int:
            q = select(func.count()).select_from(model).where(model.equipment_id == eid)
            return (await self.db.execute(q)).scalar_one()

        return EquipmentRelations(
            documents_count=await count(Document, equipment_id),
            tech_cards_count=await count(TechCard, equipment_id),
            instructions_count=await count(WorkInstruction, equipment_id),
            courses_count=await count(TwiCourse, equipment_id),
            competencies_count=await count(EquipmentCompetency, equipment_id),
        )

    async def _get_or_raise(self, equipment_id: UUID) -> Equipment:
        result = await self.db.execute(select(Equipment).where(Equipment.id == equipment_id))
        equipment = result.scalar_one_or_none()
        if equipment is None:
            raise NotFoundError("Equipment", str(equipment_id))
        return equipment
