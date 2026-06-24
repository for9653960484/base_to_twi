from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import TokenPayload, get_current_user, require_roles
from app.modules.equipment.schemas import (
    EquipmentCreate,
    EquipmentRelations,
    EquipmentResponse,
    EquipmentUpdate,
)
from app.modules.equipment.service import EquipmentService
from app.shared.schemas import PaginatedResponse

router = APIRouter()


def get_equipment_service(db: AsyncSession = Depends(get_db)) -> EquipmentService:
    return EquipmentService(db)


@router.get("/", response_model=PaginatedResponse[EquipmentResponse])
async def list_equipment(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    is_active: bool | None = None,
    user: TokenPayload = Depends(get_current_user),
    service: EquipmentService = Depends(get_equipment_service),
):
    """Список оборудования с фильтрами и поиском."""
    return await service.list(page=page, page_size=page_size, search=search, is_active=is_active)


@router.post("/", response_model=EquipmentResponse, status_code=201)
async def create_equipment(
    data: EquipmentCreate,
    user: TokenPayload = Depends(require_roles("admin", "park_owner")),
    service: EquipmentService = Depends(get_equipment_service),
):
    """Создать единицу оборудования."""
    return await service.create(data, created_by=user.sub)


@router.get("/{equipment_id}", response_model=EquipmentResponse)
async def get_equipment(
    equipment_id: UUID,
    user: TokenPayload = Depends(get_current_user),
    service: EquipmentService = Depends(get_equipment_service),
):
    """Карточка оборудования."""
    return await service.get(equipment_id)


@router.patch("/{equipment_id}", response_model=EquipmentResponse)
async def update_equipment(
    equipment_id: UUID,
    data: EquipmentUpdate,
    user: TokenPayload = Depends(require_roles("admin", "park_owner")),
    service: EquipmentService = Depends(get_equipment_service),
):
    """Обновить оборудование."""
    return await service.update(equipment_id, data)


@router.get("/{equipment_id}/relations", response_model=EquipmentRelations)
async def get_equipment_relations(
    equipment_id: UUID,
    user: TokenPayload = Depends(get_current_user),
    service: EquipmentService = Depends(get_equipment_service),
):
    """Связи: документы, инструкции, курсы, компетенции."""
    return await service.get_relations(equipment_id)
