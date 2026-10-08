from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import TokenPayload, get_current_user, require_roles
from app.modules.safety.schemas import (
    SafetyGenerateRequest,
    SafetyGenerateStatus,
    SafetySheetResponse,
    SafetySheetUpdate,
)
from app.modules.safety.service import SafetyService
from app.shared.schemas import PaginatedResponse

router = APIRouter()


def get_safety_service(db: AsyncSession = Depends(get_db)) -> SafetyService:
    return SafetyService(db)


@router.get("/", response_model=PaginatedResponse[SafetySheetResponse])
async def list_safety_sheets(
    equipment_id: UUID | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: TokenPayload = Depends(get_current_user),
    service: SafetyService = Depends(get_safety_service),
):
    return await service.list(page=page, page_size=page_size, equipment_id=equipment_id)


@router.post("/generate", response_model=SafetyGenerateStatus)
async def generate_safety_sheet(
    body: SafetyGenerateRequest,
    user: TokenPayload = Depends(require_roles("mentor", "park_owner", "admin")),
    service: SafetyService = Depends(get_safety_service),
):
    """Сформировать лист СИЗ и условий работы из оцифрованного документа."""
    return await service.generate(body.document_id, user.sub)


@router.patch("/{sheet_id}", response_model=SafetySheetResponse)
async def update_safety_sheet(
    sheet_id: UUID,
    body: SafetySheetUpdate,
    user: TokenPayload = Depends(require_roles("mentor", "park_owner", "admin")),
    service: SafetyService = Depends(get_safety_service),
):
    return await service.update(sheet_id, body)


@router.get("/export/{sheet_id}")
async def export_safety_sheet(
    sheet_id: UUID,
    user: TokenPayload = Depends(get_current_user),
    service: SafetyService = Depends(get_safety_service),
):
    """PDF листа: корпоративный шаблон или бланк письма."""
    content, filename = await service.export_pdf(sheet_id)
    encoded = quote(filename)
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=\"safety.pdf\"; filename*=UTF-8''{encoded}"},
    )


@router.get("/generate/{document_id}/status", response_model=SafetyGenerateStatus)
async def safety_generation_status(
    document_id: UUID,
    user: TokenPayload = Depends(get_current_user),
    service: SafetyService = Depends(get_safety_service),
):
    return await service.generation_status(document_id)
