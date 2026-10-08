import math
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppException, NotFoundError
from app.integrations.ai_client import get_ai_client
from app.models.brandbook import BrandbookTemplate
from app.models.ai_task import AITask
from app.models.document import Document
from app.models.equipment import Equipment
from app.models.safety import SafetySheet
from app.modules.safety.schemas import (
    PpeItem,
    SafetyGenerateStatus,
    SafetySheetResponse,
    SafetySheetUpdate,
    WorkConditions,
)
from app.shared.safety_pdf import render_safety_pdf
from app.shared.schemas import AIProcessingStatus, ContentStatus, PaginatedResponse


def _to_response(sheet: SafetySheet, equipment_name: str | None = None) -> SafetySheetResponse:
    return SafetySheetResponse(
        id=sheet.id,
        equipment_id=sheet.equipment_id,
        equipment_name=equipment_name,
        source_document_id=sheet.source_document_id,
        title=sheet.title,
        ppe=[PpeItem.model_validate(item) for item in (sheet.ppe or [])],
        work_conditions=WorkConditions.model_validate(sheet.work_conditions or {}),
        notes=sheet.notes,
        status=ContentStatus(sheet.status),
        created_at=sheet.created_at,
        updated_at=sheet.updated_at,
    )


class SafetyService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_client = get_ai_client()

    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        equipment_id: UUID | None = None,
    ) -> PaginatedResponse[SafetySheetResponse]:
        query = (
            select(SafetySheet, Equipment.name)
            .join(Equipment, Equipment.id == SafetySheet.equipment_id)
        )
        count_query = select(func.count()).select_from(SafetySheet)
        if equipment_id:
            query = query.where(SafetySheet.equipment_id == equipment_id)
            count_query = count_query.where(SafetySheet.equipment_id == equipment_id)

        total = (await self.db.execute(count_query)).scalar_one()
        query = (
            query.order_by(SafetySheet.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await self.db.execute(query)).all()
        items = [_to_response(sheet, name) for sheet, name in rows]
        pages = math.ceil(total / page_size) if total > 0 else 0
        return PaginatedResponse(
            items=items, total=total, page=page, page_size=page_size, pages=pages
        )

    async def update(self, sheet_id: UUID, data: SafetySheetUpdate) -> SafetySheetResponse:
        sheet = (
            await self.db.execute(select(SafetySheet).where(SafetySheet.id == sheet_id))
        ).scalar_one_or_none()
        if sheet is None:
            raise NotFoundError("SafetySheet", str(sheet_id))

        payload = data.model_dump(exclude_unset=True)
        if "title" in payload and payload["title"] is not None:
            payload["title"] = payload["title"].strip()
            if not payload["title"]:
                raise AppException("Укажите название документа", "TITLE_REQUIRED")
        if "equipment_id" in payload and payload["equipment_id"] is not None:
            equipment = (
                await self.db.execute(select(Equipment).where(Equipment.id == payload["equipment_id"]))
            ).scalar_one_or_none()
            if equipment is None:
                raise NotFoundError("Equipment", str(payload["equipment_id"]))
        if "notes" in payload:
            notes = (payload["notes"] or "").strip()
            payload["notes"] = notes or None

        for field, value in payload.items():
            setattr(sheet, field, value)
        sheet.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(sheet)
        equipment_name = (
            await self.db.execute(select(Equipment.name).where(Equipment.id == sheet.equipment_id))
        ).scalar_one_or_none()
        return _to_response(sheet, equipment_name)

    async def generate(self, document_id: UUID, user_id: UUID | None) -> SafetyGenerateStatus:
        doc = await self._get_document(document_id)
        if doc.ai_processing_status != AIProcessingStatus.COMPLETED.value:
            raise AppException(
                "Сначала выполните AI-обработку документа",
                "NOT_INDEXED",
                status_code=400,
            )

        ai_task = AITask(
            task_type="extract_safety",
            status="pending",
            equipment_id=doc.equipment_id,
            source_type="document",
            source_id=doc.id,
            input_payload={"document_id": str(doc.id)},
            created_by=user_id,
        )
        self.db.add(ai_task)
        await self.db.flush()

        try:
            dispatch_result = await self.ai_client.dispatch_extract_safety(
                ai_task_id=str(ai_task.id),
                document_id=str(doc.id),
                equipment_id=str(doc.equipment_id),
                created_by=str(user_id) if user_id else None,
            )
            ai_task.celery_task_id = dispatch_result.get("celery_task_id")
            ai_task.status = "processing"
            ai_task.started_at = datetime.now(timezone.utc)
            await self.db.flush()
        except AppException:
            ai_task.status = "failed"
            ai_task.error_message = "AI service unavailable"
            await self.db.flush()
            raise

        return SafetyGenerateStatus(
            document_id=doc.id,
            ai_processing_status=AIProcessingStatus.PROCESSING,
            task_id=ai_task.id,
            celery_task_id=ai_task.celery_task_id,
        )

    async def export_pdf(self, sheet_id: UUID) -> tuple[bytes, str]:
        row = (
            await self.db.execute(
                select(SafetySheet, Equipment.name)
                .join(Equipment, Equipment.id == SafetySheet.equipment_id)
                .where(SafetySheet.id == sheet_id)
            )
        ).one_or_none()
        if row is None:
            raise NotFoundError("SafetySheet", str(sheet_id))
        sheet, equipment_name = row
        template = (
            await self.db.execute(
                select(BrandbookTemplate)
                .where(
                    BrandbookTemplate.template_type == "safety_sheet",
                    BrandbookTemplate.is_active.is_(True),
                )
                .order_by(BrandbookTemplate.version.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        template_path = None
        if template is not None:
            candidate = Path(settings.storage_local_path_resolved) / template.file_path
            if candidate.is_file():
                template_path = candidate
        content = render_safety_pdf(
            equipment_name=equipment_name or "",
            title=sheet.title,
            ppe=list(sheet.ppe or []),
            work_conditions=dict(sheet.work_conditions or {}),
            notes=sheet.notes,
            template_path=template_path,
        )
        safe_name = re.sub(r'[\\/:*?"<>|]+', " ", equipment_name or "оборудование").strip()
        filename = f"Техника безопасности — {safe_name}.pdf"
        return content, filename

    async def generation_status(self, document_id: UUID) -> SafetyGenerateStatus:
        await self._get_document(document_id)
        result = await self.db.execute(
            select(AITask)
            .where(
                AITask.source_type == "document",
                AITask.source_id == document_id,
                AITask.task_type == "extract_safety",
            )
            .order_by(AITask.created_at.desc())
            .limit(1)
        )
        ai_task = result.scalar_one_or_none()
        if ai_task is None:
            return SafetyGenerateStatus(
                document_id=document_id,
                ai_processing_status=AIProcessingStatus.PENDING,
            )

        sheets_count = None
        if ai_task.result_payload:
            sheets_count = ai_task.result_payload.get("sheets_count")

        return SafetyGenerateStatus(
            document_id=document_id,
            ai_processing_status=AIProcessingStatus(ai_task.status),
            task_id=ai_task.id,
            celery_task_id=ai_task.celery_task_id,
            error_message=ai_task.error_message,
            sheets_count=sheets_count,
        )

    async def _get_document(self, document_id: UUID) -> Document:
        doc = (
            await self.db.execute(select(Document).where(Document.id == document_id))
        ).scalar_one_or_none()
        if doc is None:
            raise NotFoundError("Document", str(document_id))
        return doc
