from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user, TokenPayload
from app.models.ai_task import AITask
from app.models.document import Document
from app.modules.ai_processing.schemas import AITaskResponse, AICallbackPayload
from app.shared.schemas import MessageResponse

router = APIRouter()


@router.get("/tasks/{task_id}", response_model=AITaskResponse)
async def get_ai_task(
    task_id: UUID,
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AITask).where(AITask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return AITaskResponse(
        id=task.id,
        task_type=task.task_type,
        status=task.status,
        celery_task_id=task.celery_task_id,
        result_payload=task.result_payload,
        error_message=task.error_message,
    )


@router.post("/callback", response_model=MessageResponse)
async def ai_callback(
    body: AICallbackPayload,
    x_ai_callback_secret: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    """Webhook от AI-сервиса (опционально, worker обновляет БД напрямую)."""
    if x_ai_callback_secret != settings.AI_CALLBACK_SECRET:
        raise HTTPException(status_code=403, detail="Invalid callback secret")

    result = await db.execute(select(AITask).where(AITask.id == body.task_id))
    task = result.scalar_one_or_none()
    if task:
        task.status = body.status
        if body.result_payload:
            task.result_payload = body.result_payload
        if body.error_message:
            task.error_message = body.error_message

    if body.source_type == "document" and body.source_id:
        doc_result = await db.execute(select(Document).where(Document.id == body.source_id))
        doc = doc_result.scalar_one_or_none()
        if doc and body.document_ai_status:
            doc.ai_processing_status = body.document_ai_status

    return MessageResponse(message="OK")
