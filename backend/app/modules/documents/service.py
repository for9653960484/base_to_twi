import math
from datetime import datetime, timezone
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppException, NotFoundError
from app.integrations.ai_client import AIServiceClient, get_ai_client
from app.models.ai_task import AITask
from app.models.document import Document, DocumentVersion, DocumentVersionHistory
from app.models.equipment import Equipment
from app.shared.schemas import AIProcessingStatus, ContentStatus, PaginatedResponse
from app.shared.storage import FileStorage
from app.modules.documents.schemas import (
    AIStatusResponse,
    DocumentUpdate,
    DocumentUploadResponse,
    DocumentVersionResponse,
)


def _to_response(doc: Document, equipment_name: str | None = None) -> DocumentUploadResponse:
    version_number = None
    if doc.current_version_id and doc.versions:
        for v in doc.versions:
            if v.id == doc.current_version_id:
                version_number = v.version_number
                break

    return DocumentUploadResponse(
        id=doc.id,
        equipment_id=doc.equipment_id,
        equipment_name=equipment_name,
        title=doc.title,
        description=doc.description,
        file_path=doc.file_path,
        mime_type=doc.mime_type,
        file_size=doc.file_size,
        status=ContentStatus(doc.status),
        ai_processing_status=AIProcessingStatus(doc.ai_processing_status),
        custom_attributes=doc.custom_attributes or {},
        current_version_number=version_number,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


class DocumentService:
    def __init__(
        self,
        db: AsyncSession,
        storage: FileStorage | None = None,
        ai_client: AIServiceClient | None = None,
    ):
        self.db = db
        self.storage = storage or FileStorage()
        self.ai_client = ai_client or get_ai_client()

    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        equipment_id: UUID | None = None,
        status: str | None = None,
        search: str | None = None,
    ) -> PaginatedResponse[DocumentUploadResponse]:
        query = (
            select(Document, Equipment.name.label("equipment_name"))
            .join(Equipment, Document.equipment_id == Equipment.id)
            .options(selectinload(Document.versions))
        )
        count_query = select(func.count()).select_from(Document)

        if equipment_id:
            query = query.where(Document.equipment_id == equipment_id)
            count_query = count_query.where(Document.equipment_id == equipment_id)

        if status:
            query = query.where(Document.status == status)
            count_query = count_query.where(Document.status == status)

        if search:
            pattern = f"%{search}%"
            query = query.where(Document.title.ilike(pattern))
            count_query = count_query.where(Document.title.ilike(pattern))

        total = (await self.db.execute(count_query)).scalar_one()

        query = (
            query.order_by(Document.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await self.db.execute(query)).all()
        items = [_to_response(doc, eq_name) for doc, eq_name in rows]

        pages = math.ceil(total / page_size) if total > 0 else 0
        return PaginatedResponse(
            items=items, total=total, page=page, page_size=page_size, pages=pages
        )

    async def get(self, document_id: UUID) -> DocumentUploadResponse:
        doc, eq_name = await self._get_with_equipment(document_id)
        return _to_response(doc, eq_name)

    async def upload(
        self,
        equipment_id: UUID,
        title: str,
        file: UploadFile,
        description: str | None,
        created_by: UUID | None,
    ) -> DocumentUploadResponse:
        await self._ensure_equipment(equipment_id)

        document = Document(
            equipment_id=equipment_id,
            title=title,
            description=description,
            status=ContentStatus.DRAFT.value,
            ai_processing_status=AIProcessingStatus.PENDING.value,
            created_by=created_by,
        )
        self.db.add(document)
        await self.db.flush()

        relative_path, size, mime_type = await self.storage.save_upload(
            file, equipment_id, document.id, version=1
        )

        version = DocumentVersion(
            document_id=document.id,
            version_number=1,
            file_path=relative_path,
            change_summary="Initial upload",
            status=ContentStatus.DRAFT.value,
            created_by=created_by,
        )
        self.db.add(version)
        await self.db.flush()

        document.file_path = relative_path
        document.mime_type = mime_type
        document.file_size = size
        document.current_version_id = version.id

        await self._add_history(
            document.id, version.id, "created", created_by, "Document uploaded"
        )
        await self.db.flush()
        await self.db.refresh(document, ["versions"])

        eq_name = await self._equipment_name(equipment_id)
        return _to_response(document, eq_name)

    async def upload_new_version(
        self,
        document_id: UUID,
        file: UploadFile,
        change_summary: str | None,
        created_by: UUID | None,
    ) -> DocumentUploadResponse:
        doc, eq_name = await self._get_with_equipment(document_id)

        if doc.status == ContentStatus.ARCHIVED.value:
            raise AppException("Cannot upload version to archived document", "INVALID_STATE")

        last_version = max((v.version_number for v in doc.versions), default=0)
        new_number = last_version + 1

        relative_path, size, mime_type = await self.storage.save_upload(
            file, doc.equipment_id, doc.id, version=new_number
        )

        parent_id = doc.current_version_id
        version = DocumentVersion(
            document_id=doc.id,
            version_number=new_number,
            file_path=relative_path,
            change_summary=change_summary or f"Version {new_number}",
            status=ContentStatus.DRAFT.value,
            parent_version_id=parent_id,
            created_by=created_by,
        )
        self.db.add(version)
        await self.db.flush()

        doc.file_path = relative_path
        doc.mime_type = mime_type
        doc.file_size = size
        doc.current_version_id = version.id
        doc.status = ContentStatus.DRAFT.value
        doc.ai_processing_status = AIProcessingStatus.PENDING.value
        doc.updated_at = datetime.now(timezone.utc)

        await self._add_history(
            doc.id, version.id, "updated", created_by, change_summary or "New version uploaded"
        )
        await self.db.flush()
        await self.db.refresh(doc, ["versions"])
        return _to_response(doc, eq_name)

    async def update(
        self, document_id: UUID, data: DocumentUpdate
    ) -> DocumentUploadResponse:
        doc, eq_name = await self._get_with_equipment(document_id)
        update_data = data.model_dump(exclude_unset=True)

        if "equipment_id" in update_data and update_data["equipment_id"] is not None:
            new_eq = update_data["equipment_id"]
            if new_eq != doc.equipment_id:
                if doc.status != ContentStatus.DRAFT.value:
                    raise AppException(
                        "Equipment can only be changed for draft documents", "INVALID_STATE"
                    )
                await self._ensure_equipment(new_eq)
                doc.equipment_id = new_eq
                eq_name = await self._equipment_name(new_eq)
            del update_data["equipment_id"]

        if "custom_attributes" in update_data and update_data["custom_attributes"] is not None:
            merged = {**(doc.custom_attributes or {}), **update_data["custom_attributes"]}
            update_data["custom_attributes"] = merged

        for field, value in update_data.items():
            setattr(doc, field, value)

        doc.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return _to_response(doc, eq_name)

    async def list_versions(self, document_id: UUID) -> list[DocumentVersionResponse]:
        doc, _ = await self._get_with_equipment(document_id)
        return [
            DocumentVersionResponse(
                id=v.id,
                version_number=v.version_number,
                status=ContentStatus(v.status),
                change_summary=v.change_summary,
                created_at=v.created_at,
            )
            for v in sorted(doc.versions, key=lambda x: x.version_number, reverse=True)
        ]

    async def get_file_path(self, document_id: UUID) -> tuple[str, str, str | None]:
        """Возвращает (absolute_path, filename, mime_type) для скачивания."""
        doc, _ = await self._get_with_equipment(document_id)
        if not doc.file_path:
            raise AppException("Document has no file", "NO_FILE", 404)
        full = self.storage.resolve_path(doc.file_path)
        if not full.is_file():
            raise AppException("File not found on disk", "FILE_NOT_FOUND", 404)
        return str(full), full.name, doc.mime_type

    async def start_ai_processing(
        self, document_id: UUID, force_reprocess: bool = False, user_id: UUID | None = None
    ) -> AIStatusResponse:
        doc, _ = await self._get_with_equipment(document_id)

        if not doc.file_path:
            raise AppException("Document has no file to process", "NO_FILE")

        if doc.ai_processing_status == AIProcessingStatus.PROCESSING.value and not force_reprocess:
            return await self.get_ai_status(document_id)

        if force_reprocess:
            doc.ai_processing_status = AIProcessingStatus.PENDING.value

        ai_task = AITask(
            task_type="document_parse",
            status="pending",
            equipment_id=doc.equipment_id,
            source_type="document",
            source_id=doc.id,
            input_payload={
                "file_path": doc.file_path,
                "title": doc.title,
            },
            created_by=user_id,
        )
        self.db.add(ai_task)
        await self.db.flush()

        doc.ai_processing_status = AIProcessingStatus.PROCESSING.value
        doc.updated_at = datetime.now(timezone.utc)
        await self.db.flush()

        try:
            dispatch_result = await self.ai_client.dispatch_document_pipeline(
                ai_task_id=str(ai_task.id),
                document_id=str(doc.id),
                equipment_id=str(doc.equipment_id),
                file_path=doc.file_path,
                title=doc.title,
            )
            ai_task.celery_task_id = dispatch_result.get("celery_task_id")
            ai_task.status = "processing"
            ai_task.started_at = datetime.now(timezone.utc)
            await self.db.flush()
        except AppException:
            doc.ai_processing_status = AIProcessingStatus.FAILED.value
            ai_task.status = "failed"
            ai_task.error_message = "AI service unavailable"
            await self.db.flush()
            raise

        return AIStatusResponse(
            document_id=doc.id,
            ai_processing_status=AIProcessingStatus.PROCESSING,
            task_id=ai_task.id,
            celery_task_id=ai_task.celery_task_id,
        )

    async def get_ai_status(self, document_id: UUID) -> AIStatusResponse:
        doc, _ = await self._get_with_equipment(document_id)

        task_result = await self.db.execute(
            select(AITask)
            .where(AITask.source_type == "document", AITask.source_id == document_id)
            .order_by(AITask.created_at.desc())
            .limit(1)
        )
        ai_task = task_result.scalar_one_or_none()

        result_summary = None
        maintenance_count = None
        error_message = None
        task_id = None
        celery_task_id = None

        if ai_task:
            task_id = ai_task.id
            celery_task_id = ai_task.celery_task_id
            error_message = ai_task.error_message
            if ai_task.result_payload:
                analysis = ai_task.result_payload.get("analysis", {})
                result_summary = analysis.get("summary") or ai_task.result_payload.get("summary")
                works = analysis.get("maintenance_works", [])
                maintenance_count = len(works) if isinstance(works, list) else None

        return AIStatusResponse(
            document_id=doc.id,
            ai_processing_status=AIProcessingStatus(doc.ai_processing_status),
            task_id=task_id,
            celery_task_id=celery_task_id,
            result_summary=result_summary,
            error_message=error_message,
            maintenance_works_count=maintenance_count,
        )

    async def submit_for_approval(
        self, document_id: UUID, user_id: UUID | None
    ) -> None:
        doc, _ = await self._get_with_equipment(document_id)
        if doc.status != ContentStatus.DRAFT.value:
            raise AppException("Only draft documents can be submitted", "INVALID_STATE")

        doc.status = ContentStatus.PENDING_APPROVAL.value
        doc.updated_at = datetime.now(timezone.utc)

        if doc.current_version_id:
            version = next((v for v in doc.versions if v.id == doc.current_version_id), None)
            if version:
                version.status = ContentStatus.PENDING_APPROVAL.value
                await self._add_history(
                    doc.id, version.id, "submitted", user_id, "Submitted for approval"
                )

        await self.db.flush()

    async def approve(self, document_id: UUID, user_id: UUID | None) -> None:
        doc, _ = await self._get_with_equipment(document_id)
        if doc.status != ContentStatus.PENDING_APPROVAL.value:
            raise AppException("Document is not pending approval", "INVALID_STATE")

        doc.status = ContentStatus.PUBLISHED.value
        doc.updated_at = datetime.now(timezone.utc)

        if doc.current_version_id:
            version = next((v for v in doc.versions if v.id == doc.current_version_id), None)
            if version:
                version.status = ContentStatus.PUBLISHED.value
                await self._add_history(
                    doc.id, version.id, "approved", user_id, "Document approved"
                )

        await self.db.flush()

    async def archive(self, document_id: UUID, user_id: UUID | None) -> None:
        doc, _ = await self._get_with_equipment(document_id)
        doc.status = ContentStatus.ARCHIVED.value
        doc.updated_at = datetime.now(timezone.utc)

        if doc.current_version_id:
            version = next((v for v in doc.versions if v.id == doc.current_version_id), None)
            if version:
                version.status = ContentStatus.ARCHIVED.value
                await self._add_history(doc.id, version.id, "archived", user_id, "Archived")

        await self.db.flush()

    async def _get_with_equipment(self, document_id: UUID) -> tuple[Document, str]:
        result = await self.db.execute(
            select(Document, Equipment.name)
            .join(Equipment, Document.equipment_id == Equipment.id)
            .where(Document.id == document_id)
            .options(selectinload(Document.versions))
        )
        row = result.one_or_none()
        if row is None:
            raise NotFoundError("Document", str(document_id))
        return row[0], row[1]

    async def _ensure_equipment(self, equipment_id: UUID) -> None:
        result = await self.db.execute(
            select(Equipment.id).where(Equipment.id == equipment_id, Equipment.is_active == True)
        )
        if result.scalar_one_or_none() is None:
            raise NotFoundError("Equipment", str(equipment_id))

    async def _equipment_name(self, equipment_id: UUID) -> str:
        result = await self.db.execute(
            select(Equipment.name).where(Equipment.id == equipment_id)
        )
        name = result.scalar_one_or_none()
        return name or ""

    async def _add_history(
        self,
        document_id: UUID,
        version_id: UUID,
        action: str,
        performed_by: UUID | None,
        comment: str | None = None,
    ) -> None:
        self.db.add(
            DocumentVersionHistory(
                document_id=document_id,
                version_id=version_id,
                action=action,
                performed_by=performed_by,
                comment=comment,
            )
        )
