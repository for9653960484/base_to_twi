from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.core.security import get_current_user, require_roles, TokenPayload
from app.modules.knowledge.schemas import KnowledgeSearchRequest, KnowledgeSearchResponse
from app.modules.knowledge.service import KnowledgeService
from app.shared.schemas import MessageResponse
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


def get_knowledge_service(db: AsyncSession = Depends(get_db)) -> KnowledgeService:
    return KnowledgeService(db)


@router.post("/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(
    body: KnowledgeSearchRequest,
    user: TokenPayload = Depends(get_current_user),
    service: KnowledgeService = Depends(get_knowledge_service),
):
    """Q&A поиск по базе знаний (векторный + LLM)."""
    return await service.search(body.query, body.equipment_id, body.top_k)


@router.post("/reindex", response_model=MessageResponse)
async def reindex_knowledge(user: TokenPayload = Depends(require_roles("admin"))):
    return MessageResponse(message="Use document AI processing to reindex sources")
