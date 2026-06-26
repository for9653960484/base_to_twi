from typing import Literal
from uuid import UUID
from urllib.parse import quote

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import TokenPayload, get_current_user
from app.modules.tech_cards.schemas import TechCardCreate, TechCardResponse, TechCardUpdate
from app.modules.tech_cards.service import TechCardService
from app.shared.schemas import ContentStatus, MaintenanceType, PaginatedResponse

router = APIRouter()


def get_tech_card_service(db: AsyncSession = Depends(get_db)) -> TechCardService:
    return TechCardService(db)


@router.get("/", response_model=PaginatedResponse[TechCardResponse])
async def list_tech_cards(
    equipment_id: UUID | None = None,
    maintenance_type: MaintenanceType | None = None,
    status: ContentStatus | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: TokenPayload = Depends(get_current_user),
    service: TechCardService = Depends(get_tech_card_service),
):
    return await service.list(
        page=page,
        page_size=page_size,
        equipment_id=equipment_id,
        maintenance_type=maintenance_type,
        status=status,
    )


@router.post("/", response_model=TechCardResponse, status_code=201)
async def create_tech_card(
    data: TechCardCreate,
    user: TokenPayload = Depends(get_current_user),
    service: TechCardService = Depends(get_tech_card_service),
):
    return await service.create(data, created_by=user.sub)


@router.get("/export/{tech_card_id}")
async def export_tech_card(
    tech_card_id: UUID,
    format: Literal["pdf", "docx"] = Query("pdf", alias="format"),
    user: TokenPayload = Depends(get_current_user),
    service: TechCardService = Depends(get_tech_card_service),
):
    if format == "docx":
        content, filename = await service.export_docx(tech_card_id)
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    else:
        content, filename = await service.export_pdf(tech_card_id)
        media_type = "application/pdf"
    encoded = quote(filename)
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename=\"{encoded}\"; filename*=UTF-8''{encoded}"},
    )


@router.get("/{tech_card_id}", response_model=TechCardResponse)
async def get_tech_card(
    tech_card_id: UUID,
    user: TokenPayload = Depends(get_current_user),
    service: TechCardService = Depends(get_tech_card_service),
):
    return await service.get(tech_card_id)


@router.patch("/{tech_card_id}", response_model=TechCardResponse)
async def update_tech_card(
    tech_card_id: UUID,
    data: TechCardUpdate,
    user: TokenPayload = Depends(get_current_user),
    service: TechCardService = Depends(get_tech_card_service),
):
    return await service.update(tech_card_id, data)
