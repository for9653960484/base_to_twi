from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.security import get_current_user, require_roles, TokenPayload
from app.modules.instructions.schemas import (
    AIGenerateRequest,
    InstructionCreate,
    InstructionResponse,
    InstructionStepsUpdate,
)
from app.shared.schemas import MessageResponse, PaginatedResponse

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[InstructionResponse])
async def list_instructions(
    equipment_id: UUID | None = None,
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: TokenPayload = Depends(get_current_user),
):
    return PaginatedResponse(items=[], total=0, page=page, page_size=page_size, pages=0)


@router.post("/", response_model=InstructionResponse, status_code=201)
async def create_instruction(
    data: InstructionCreate,
    user: TokenPayload = Depends(require_roles("mentor", "park_owner", "admin")),
):
    raise NotImplementedError


@router.get("/{instruction_id}", response_model=InstructionResponse)
async def get_instruction(instruction_id: UUID, user: TokenPayload = Depends(get_current_user)):
    raise NotImplementedError


@router.put("/{instruction_id}/steps", response_model=InstructionResponse)
async def update_steps(
    instruction_id: UUID,
    data: InstructionStepsUpdate,
    user: TokenPayload = Depends(require_roles("mentor", "park_owner", "admin")),
):
    """Редактор структуры: шаги — ключевые моменты — причины."""
    raise NotImplementedError


@router.post("/{instruction_id}/ai-generate", response_model=InstructionResponse)
async def ai_generate_instruction(
    instruction_id: UUID,
    body: AIGenerateRequest,
    user: TokenPayload = Depends(require_roles("mentor", "park_owner", "admin")),
):
    raise NotImplementedError


@router.post("/{instruction_id}/submit", response_model=MessageResponse)
async def submit_instruction(instruction_id: UUID, user: TokenPayload = Depends(require_roles("mentor"))):
    raise NotImplementedError


@router.post("/{instruction_id}/approve", response_model=MessageResponse)
async def approve_instruction(
    instruction_id: UUID, user: TokenPayload = Depends(require_roles("park_owner", "admin"))
):
    raise NotImplementedError


@router.post("/{instruction_id}/generate-document")
async def generate_corporate_document(
    instruction_id: UUID, user: TokenPayload = Depends(require_roles("mentor", "park_owner", "admin"))
):
    """Формирование инструкции по корпоративному шаблону."""
    raise NotImplementedError
