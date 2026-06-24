from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.security import get_current_user, require_roles, TokenPayload
from app.modules.competencies.schemas import (
    AssessRequest,
    CompetencyGapReport,
    CompetencyMatrix,
    CompetencyResponse,
)
from app.shared.schemas import MessageResponse

router = APIRouter()


@router.get("/matrix", response_model=CompetencyMatrix)
async def get_competency_matrix(
    equipment_id: UUID | None = None,
    department_id: UUID | None = None,
    user: TokenPayload = Depends(get_current_user),
):
    """Матрица компетенций с фильтрами."""
    return CompetencyMatrix(equipment_id=equipment_id, department_id=department_id, cells=[])


@router.get("/gaps", response_model=list[CompetencyGapReport])
async def get_competency_gaps(
    equipment_id: UUID | None = None,
    user: TokenPayload = Depends(get_current_user),
):
    """Аналитика дефицита компетенций."""
    return []


@router.post("/assess", response_model=MessageResponse)
async def assess_competency(
    body: AssessRequest,
    user: TokenPayload = Depends(require_roles("mentor", "park_owner", "admin")),
):
    raise NotImplementedError


@router.get("/reports/summary")
async def competency_summary_report(user: TokenPayload = Depends(get_current_user)):
    raise NotImplementedError
