from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.security import get_current_user, TokenPayload
from app.modules.maintenance_calendar.schemas import CalendarEntry, CalendarGenerateRequest
from app.shared.schemas import MessageResponse

router = APIRouter()


@router.get("/", response_model=list[CalendarEntry])
async def get_calendar(
    target_date: date | None = Query(None, alias="date"),
    equipment_id: UUID | None = None,
    user: TokenPayload = Depends(get_current_user),
):
    """Сводный график ТО на дату."""
    return []


@router.post("/generate", response_model=MessageResponse)
async def generate_calendar(
    body: CalendarGenerateRequest,
    user: TokenPayload = Depends(get_current_user),
):
    """Пересчёт календаря из технологических карт."""
    raise NotImplementedError
