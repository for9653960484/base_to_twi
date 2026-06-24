from fastapi import APIRouter, Depends, Request

from app.core.security import require_roles, TokenPayload
from app.modules.hr.schemas import HRSyncRequest, HRSyncStatus
from app.shared.schemas import MessageResponse

router = APIRouter()


@router.post("/sync", response_model=HRSyncStatus)
async def sync_hr(
    body: HRSyncRequest = HRSyncRequest(),
    user: TokenPayload = Depends(require_roles("admin", "hr")),
):
    """Импорт сотрудников, ролей, подразделений из HR-системы."""
    raise NotImplementedError


@router.get("/sync/status", response_model=HRSyncStatus)
async def get_sync_status(user: TokenPayload = Depends(require_roles("admin", "hr"))):
    return HRSyncStatus()


@router.post("/webhook", response_model=MessageResponse)
async def hr_webhook(request: Request):
    """Webhook от внешней HR-системы."""
    raise NotImplementedError
