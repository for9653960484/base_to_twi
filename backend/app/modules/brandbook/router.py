from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.core.security import require_roles, TokenPayload
from app.modules.brandbook.schemas import BrandbookTemplateResponse

router = APIRouter()


@router.get("/templates", response_model=list[BrandbookTemplateResponse])
async def list_templates(user: TokenPayload = Depends(require_roles("admin", "park_owner", "mentor"))):
    return []


@router.post("/templates", response_model=BrandbookTemplateResponse, status_code=201)
async def upload_template(
    title: str = Form(...),
    template_type: str = Form(...),
    file: UploadFile = File(...),
    user: TokenPayload = Depends(require_roles("admin")),
):
    raise NotImplementedError
