from pathlib import Path
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppException
from app.models.brandbook import BrandbookTemplate
from app.modules.brandbook.schemas import BrandbookTemplateResponse

SAFETY_TEMPLATE_TYPE = "safety_sheet"
TECH_CARD_TEMPLATE_TYPE = "tech_card"
ALLOWED_TEMPLATE_EXT = {".docx"}

TEMPLATE_SPECS: dict[str, dict] = {
    SAFETY_TEMPLATE_TYPE: {
        "title": "Шаблон листа техники безопасности",
        "path": "templates/brandbook/safety_sheet_v{version}.docx",
        "placeholders": [
            "{{EQUIPMENT_NAME}}",
            "{{TITLE}}",
            "{{GENERATED_AT}}",
            "{{PPE_BLOCK}}",
            "{{CONDITIONS_BLOCK}}",
            "{{NOTES}}",
        ],
    },
    TECH_CARD_TEMPLATE_TYPE: {
        "title": "Шаблон технологической карты",
        "path": "templates/brandbook/tech_card_v{version}.docx",
        "placeholders": [
            "{{EQUIPMENT_NAME}}",
            "{{TITLE}}",
            "{{MAINTENANCE_TYPE}}",
            "{{GENERATED_AT}}",
            "{{WORK_ITEMS_BLOCK}}",
        ],
    },
}


def _to_response(row: BrandbookTemplate) -> BrandbookTemplateResponse:
    return BrandbookTemplateResponse(
        id=row.id,
        title=row.title,
        template_type=row.template_type,
        file_path=row.file_path,
        file_name=Path(row.file_path).name,
        version=row.version,
        is_active=row.is_active,
    )


class BrandbookService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(self, template_type: str | None = None) -> list[BrandbookTemplateResponse]:
        query = select(BrandbookTemplate).order_by(BrandbookTemplate.created_at.desc())
        if template_type:
            query = query.where(BrandbookTemplate.template_type == template_type)
        rows = (await self.db.execute(query)).scalars().all()
        return [_to_response(row) for row in rows]

    async def active_safety_template(self) -> BrandbookTemplate | None:
        result = await self.db.execute(
            select(BrandbookTemplate)
            .where(
                BrandbookTemplate.template_type == SAFETY_TEMPLATE_TYPE,
                BrandbookTemplate.is_active.is_(True),
            )
            .order_by(BrandbookTemplate.version.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def upload(
        self,
        *,
        title: str,
        template_type: str,
        file: UploadFile,
        created_by: UUID | None,
    ) -> BrandbookTemplateResponse:
        spec = TEMPLATE_SPECS.get(template_type)
        if spec is None:
            raise AppException(
                "Можно загрузить шаблон листа техники безопасности или технологической карты",
                "UNSUPPORTED_TEMPLATE",
            )
        if not file.filename:
            raise AppException("Укажите файл шаблона", "FILE_REQUIRED")
        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_TEMPLATE_EXT:
            raise AppException("Шаблон должен быть в формате DOCX", "UNSUPPORTED_FILE")

        content = await file.read()
        if not content:
            raise AppException("Файл шаблона пустой", "EMPTY_FILE")
        if len(content) > 20 * 1024 * 1024:
            raise AppException("Файл шаблона больше 20 МБ", "FILE_TOO_LARGE")

        current = await self.db.scalar(
            select(func.max(BrandbookTemplate.version)).where(
                BrandbookTemplate.template_type == template_type
            )
        )
        version = int(current or 0) + 1
        relative = spec["path"].format(version=version)
        dest = Path(settings.storage_local_path_resolved) / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)

        await self.db.execute(
            update(BrandbookTemplate)
            .where(
                BrandbookTemplate.template_type == template_type,
                BrandbookTemplate.is_active.is_(True),
            )
            .values(is_active=False)
        )
        row = BrandbookTemplate(
            title=title.strip() or spec["title"],
            template_type=template_type,
            file_path=relative,
            version=version,
            is_active=True,
            metadata_={"placeholders": spec["placeholders"]},
            created_by=created_by,
        )
        self.db.add(row)
        await self.db.flush()
        return _to_response(row)
