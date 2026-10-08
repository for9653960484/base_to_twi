from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from urllib.parse import quote

from app.core.database import get_db
from app.core.security import TokenPayload, get_current_user, require_roles
from app.modules.brandbook.schemas import BrandbookTemplateResponse
from app.modules.brandbook.service import SAFETY_TEMPLATE_TYPE, BrandbookService
from app.shared.brandbook_export import build_sample_tech_card_template
from app.shared.safety_pdf import build_sample_safety_template

router = APIRouter()


def get_brandbook_service(db: AsyncSession = Depends(get_db)) -> BrandbookService:
    return BrandbookService(db)


@router.get("/templates/safety-sheet/sample")
async def download_safety_template_sample(
    user: TokenPayload = Depends(get_current_user),
):
    """Образец DOCX-шаблона листа техники безопасности."""
    content = build_sample_safety_template()
    filename = "Шаблон листа техники безопасности.docx"
    encoded = quote(filename)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename=\"sample.docx\"; filename*=UTF-8''{encoded}"},
    )


@router.get("/templates/tech-card/sample")
async def download_tech_card_template_sample(
    user: TokenPayload = Depends(get_current_user),
):
    """Образец DOCX-шаблона технологической карты."""
    content = build_sample_tech_card_template()
    filename = "Шаблон технологической карты.docx"
    encoded = quote(filename)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename=\"sample.docx\"; filename*=UTF-8''{encoded}"},
    )


@router.get("/templates", response_model=list[BrandbookTemplateResponse])
async def list_templates(
    template_type: str | None = Query(None),
    user: TokenPayload = Depends(get_current_user),
    service: BrandbookService = Depends(get_brandbook_service),
):
    return await service.list(template_type)


@router.post("/templates", response_model=BrandbookTemplateResponse, status_code=201)
async def upload_template(
    title: str = Form("Шаблон листа техники безопасности"),
    template_type: str = Form(SAFETY_TEMPLATE_TYPE),
    file: UploadFile = File(...),
    user: TokenPayload = Depends(require_roles("mentor", "park_owner", "admin")),
    service: BrandbookService = Depends(get_brandbook_service),
):
    return await service.upload(
        title=title,
        template_type=template_type,
        file=file,
        created_by=user.sub,
    )
