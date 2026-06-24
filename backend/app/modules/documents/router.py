from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AppException
from app.core.security import TokenPayload, get_current_user, require_roles
from app.modules.documents.schemas import (
    AIProcessRequest,
    AIStatusResponse,
    DocumentUpdate,
    DocumentUploadResponse,
    DocumentVersionResponse,
)
from app.modules.documents.service import DocumentService
from app.shared.schemas import MessageResponse, PaginatedResponse
from app.shared.storage import FileStorage, get_storage

router = APIRouter()


def get_document_service(
    db: AsyncSession = Depends(get_db),
    storage: FileStorage = Depends(get_storage),
) -> DocumentService:
    return DocumentService(db, storage)


@router.get("/", response_model=PaginatedResponse[DocumentUploadResponse])
async def list_documents(
    equipment_id: UUID | None = None,
    status: str | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: TokenPayload = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):
    """Список документов с фильтрами."""
    return await service.list(
        page=page,
        page_size=page_size,
        equipment_id=equipment_id,
        status=status,
        search=search,
    )


@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    equipment_id: UUID = Form(...),
    title: str = Form(...),
    description: str | None = Form(None),
    file: UploadFile = File(...),
    user: TokenPayload = Depends(require_roles("mentor", "park_owner", "admin")),
    service: DocumentService = Depends(get_document_service),
):
    """Загрузка заводской документации с привязкой к оборудованию."""
    try:
        return await service.upload(
            equipment_id=equipment_id,
            title=title,
            file=file,
            description=description,
            created_by=user.sub,
        )
    except ValueError as e:
        raise AppException(str(e), "VALIDATION_ERROR")


@router.get("/{document_id}", response_model=DocumentUploadResponse)
async def get_document(
    document_id: UUID,
    user: TokenPayload = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):
    return await service.get(document_id)


@router.patch("/{document_id}", response_model=DocumentUploadResponse)
async def update_document(
    document_id: UUID,
    data: DocumentUpdate,
    user: TokenPayload = Depends(require_roles("mentor", "park_owner", "admin")),
    service: DocumentService = Depends(get_document_service),
):
    return await service.update(document_id, data)


@router.get("/{document_id}/download")
async def download_document(
    document_id: UUID,
    user: TokenPayload = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):
    """Скачать текущую версию файла."""
    path, filename, mime_type = await service.get_file_path(document_id)
    return FileResponse(
        path,
        filename=filename,
        media_type=mime_type or "application/octet-stream",
    )


@router.get("/{document_id}/versions", response_model=list[DocumentVersionResponse])
async def list_versions(
    document_id: UUID,
    user: TokenPayload = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):
    return await service.list_versions(document_id)


@router.post("/{document_id}/versions", response_model=DocumentUploadResponse, status_code=201)
async def upload_new_version(
    document_id: UUID,
    file: UploadFile = File(...),
    change_summary: str | None = Form(None),
    user: TokenPayload = Depends(require_roles("mentor", "park_owner", "admin")),
    service: DocumentService = Depends(get_document_service),
):
    """Загрузить новую версию документа."""
    try:
        return await service.upload_new_version(
            document_id, file, change_summary, created_by=user.sub
        )
    except ValueError as e:
        raise AppException(str(e), "VALIDATION_ERROR")


@router.post("/{document_id}/ai-process", response_model=AIStatusResponse)
async def start_ai_processing(
    document_id: UUID,
    body: AIProcessRequest = AIProcessRequest(),
    user: TokenPayload = Depends(require_roles("mentor", "park_owner", "admin")),
    service: DocumentService = Depends(get_document_service),
):
    return await service.start_ai_processing(document_id, body.force_reprocess, user.sub)


@router.get("/{document_id}/ai-status", response_model=AIStatusResponse)
async def get_ai_status(
    document_id: UUID,
    user: TokenPayload = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):
    return await service.get_ai_status(document_id)


@router.post("/{document_id}/submit", response_model=MessageResponse)
async def submit_for_approval(
    document_id: UUID,
    user: TokenPayload = Depends(require_roles("mentor", "park_owner", "admin")),
    service: DocumentService = Depends(get_document_service),
):
    await service.submit_for_approval(document_id, user.sub)
    return MessageResponse(message="Document submitted for approval")


@router.post("/{document_id}/approve", response_model=MessageResponse)
async def approve_document(
    document_id: UUID,
    user: TokenPayload = Depends(require_roles("park_owner", "admin")),
    service: DocumentService = Depends(get_document_service),
):
    await service.approve(document_id, user.sub)
    return MessageResponse(message="Document approved")


@router.post("/{document_id}/archive", response_model=MessageResponse)
async def archive_document(
    document_id: UUID,
    user: TokenPayload = Depends(require_roles("park_owner", "admin")),
    service: DocumentService = Depends(get_document_service),
):
    await service.archive(document_id, user.sub)
    return MessageResponse(message="Document archived")
