import math
from pathlib import Path
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException, NotFoundError
from app.models.brandbook import BrandbookTemplate
from app.models.equipment import Equipment
from app.models.tech_card import TechCard
from app.modules.tech_cards.schemas import TechCardCreate, TechCardResponse, TechCardUpdate
from app.shared.brandbook_export import ensure_default_tech_card_template, render_tech_card_docx
from app.shared.brandbook_pdf import render_tech_card_pdf
from app.shared.schemas import ContentStatus, MaintenanceType, PaginatedResponse

MAINTENANCE_TYPE_ORDER: dict[str, int] = {
    MaintenanceType.DAILY.value: 0,
    MaintenanceType.WEEKLY.value: 1,
    MaintenanceType.MONTHLY.value: 2,
    MaintenanceType.QUARTERLY.value: 3,
    MaintenanceType.SEMI_ANNUAL.value: 4,
    MaintenanceType.ANNUAL.value: 5,
}


def _to_response(card: TechCard, equipment_name: str | None = None) -> TechCardResponse:
    from app.modules.tech_cards.schemas import WorkItem

    items = [WorkItem.model_validate(wi) for wi in (card.work_items or [])]
    return TechCardResponse(
        id=card.id,
        equipment_id=card.equipment_id,
        equipment_name=equipment_name,
        maintenance_type=MaintenanceType(card.maintenance_type),
        title=card.title,
        work_items=items,
        status=ContentStatus(card.status),
        created_at=card.created_at,
        updated_at=card.updated_at,
    )


class TechCardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        equipment_id: UUID | None = None,
        maintenance_type: MaintenanceType | None = None,
        status: ContentStatus | None = None,
    ) -> PaginatedResponse[TechCardResponse]:
        query = (
            select(TechCard, Equipment.name)
            .join(Equipment, Equipment.id == TechCard.equipment_id)
        )
        count_query = select(func.count()).select_from(TechCard)

        if equipment_id:
            query = query.where(TechCard.equipment_id == equipment_id)
            count_query = count_query.where(TechCard.equipment_id == equipment_id)
        if maintenance_type:
            query = query.where(TechCard.maintenance_type == maintenance_type.value)
            count_query = count_query.where(TechCard.maintenance_type == maintenance_type.value)
        if status:
            query = query.where(TechCard.status == status.value)
            count_query = count_query.where(TechCard.status == status.value)

        total = (await self.db.execute(count_query)).scalar_one()
        query = query.offset((page - 1) * page_size).limit(page_size)
        rows = (await self.db.execute(query)).all()
        rows = sorted(
            rows,
            key=lambda row: (
                MAINTENANCE_TYPE_ORDER.get(row[0].maintenance_type, 99),
                row[0].title,
            ),
        )
        items = [_to_response(card, eq_name) for card, eq_name in rows]
        pages = math.ceil(total / page_size) if total > 0 else 0
        return PaginatedResponse(
            items=items, total=total, page=page, page_size=page_size, pages=pages
        )

    async def get(self, tech_card_id: UUID) -> TechCardResponse:
        row = await self._fetch_row(tech_card_id)
        return _to_response(row[0], row[1])

    async def create(self, data: TechCardCreate, created_by: UUID | None) -> TechCardResponse:
        await self._ensure_equipment(data.equipment_id)
        card = TechCard(
            equipment_id=data.equipment_id,
            maintenance_type=data.maintenance_type.value,
            title=data.title,
            work_items=[wi.model_dump() for wi in data.work_items],
            created_by=created_by,
        )
        self.db.add(card)
        await self.db.flush()
        eq_name = await self._equipment_name(data.equipment_id)
        return _to_response(card, eq_name)

    async def update(self, tech_card_id: UUID, data: TechCardUpdate) -> TechCardResponse:
        card, eq_name = await self._fetch_row(tech_card_id)
        if data.title is not None:
            card.title = data.title
        if data.maintenance_type is not None:
            card.maintenance_type = data.maintenance_type.value
        if data.work_items is not None:
            card.work_items = [wi.model_dump() for wi in data.work_items]
        if data.status is not None:
            card.status = data.status.value
        await self.db.flush()
        return _to_response(card, eq_name)

    async def export_docx(self, tech_card_id: UUID) -> tuple[bytes, str]:
        card, eq_name = await self._fetch_row(tech_card_id)
        self._ensure_exportable(card)
        template_path = await self._active_template_path()
        content = render_tech_card_docx(
            Path(template_path),
            equipment_name=eq_name or str(card.equipment_id),
            title=card.title,
            maintenance_type=card.maintenance_type,
            work_items=card.work_items or [],
        )
        filename = f"tech_card_{self._safe_filename(card, tech_card_id)}.docx"
        return content, filename

    async def export_pdf(self, tech_card_id: UUID) -> tuple[bytes, str]:
        card, eq_name = await self._fetch_row(tech_card_id)
        self._ensure_exportable(card)
        content = render_tech_card_pdf(
            equipment_name=eq_name or str(card.equipment_id),
            title=card.title,
            maintenance_type=card.maintenance_type,
            work_items=card.work_items or [],
        )
        filename = f"tech_card_{self._safe_filename(card, tech_card_id)}.pdf"
        return content, filename

    def _ensure_exportable(self, card: TechCard) -> None:
        if card.status != ContentStatus.PUBLISHED.value:
            raise AppException(
                "Технологическая карта не согласована и недоступна для выгрузки",
                code="NOT_APPROVED",
                status_code=403,
            )

    @staticmethod
    def _safe_filename(card: TechCard, tech_card_id: UUID) -> str:
        safe_name = "".join(
            c if ord(c) < 128 and (c.isalnum() or c in " _-") else "_"
            for c in card.title
        )[:60].strip("_ ")
        return safe_name or str(tech_card_id)[:8]

    async def _active_template_path(self) -> Path:
        result = await self.db.execute(
            select(BrandbookTemplate)
            .where(
                BrandbookTemplate.template_type == "tech_card",
                BrandbookTemplate.is_active.is_(True),
            )
            .order_by(BrandbookTemplate.version.desc())
            .limit(1)
        )
        template = result.scalar_one_or_none()
        if template:
            from app.core.config import settings

            path = Path(settings.storage_local_path_resolved) / template.file_path
            if path.is_file():
                return path
        return ensure_default_tech_card_template()

    async def _fetch_row(self, tech_card_id: UUID) -> tuple[TechCard, str]:
        result = await self.db.execute(
            select(TechCard, Equipment.name)
            .join(Equipment, Equipment.id == TechCard.equipment_id)
            .where(TechCard.id == tech_card_id)
        )
        row = result.one_or_none()
        if not row:
            raise NotFoundError("Tech card not found")
        return row[0], row[1]

    async def _ensure_equipment(self, equipment_id: UUID) -> None:
        exists = await self.db.execute(
            select(Equipment.id).where(Equipment.id == equipment_id)
        )
        if not exists.scalar_one_or_none():
            raise NotFoundError("Equipment not found")

    async def _equipment_name(self, equipment_id: UUID) -> str:
        result = await self.db.execute(
            select(Equipment.name).where(Equipment.id == equipment_id)
        )
        return result.scalar_one()
