from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.security import get_current_user, TokenPayload
from app.modules.tech_cards.schemas import TechCardCreate, TechCardResponse
from app.shared.schemas import MaintenanceType, MessageResponse, PaginatedResponse

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[TechCardResponse])
async def list_tech_cards(
    equipment_id: UUID | None = None,
    maintenance_type: MaintenanceType | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: TokenPayload = Depends(get_current_user),
):
    return PaginatedResponse(items=[], total=0, page=page, page_size=page_size, pages=0)


@router.post("/", response_model=TechCardResponse, status_code=201)
async def create_tech_card(data: TechCardCreate, user: TokenPayload = Depends(get_current_user)):
    raise NotImplementedError


@router.get("/{tech_card_id}", response_model=TechCardResponse)
async def get_tech_card(tech_card_id: UUID, user: TokenPayload = Depends(get_current_user)):
    raise NotImplementedError


@router.get("/export/{tech_card_id}")
async def export_tech_card(tech_card_id: UUID, user: TokenPayload = Depends(get_current_user)):
    """Выгрузка в корпоративном формате."""
    raise NotImplementedError
