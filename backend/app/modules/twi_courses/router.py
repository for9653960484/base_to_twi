from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.security import get_current_user, require_roles, TokenPayload
from app.modules.twi_courses.schemas import (
    CourseAssignRequest,
    CourseAssignmentResponse,
    CourseCreate,
    CourseResponse,
)
from app.shared.schemas import MessageResponse, PaginatedResponse

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[CourseResponse])
async def list_courses(
    equipment_id: UUID | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: TokenPayload = Depends(get_current_user),
):
    return PaginatedResponse(items=[], total=0, page=page, page_size=page_size, pages=0)


@router.post("/", response_model=CourseResponse, status_code=201)
async def create_course_from_instruction(
    data: CourseCreate,
    user: TokenPayload = Depends(require_roles("mentor", "park_owner", "admin")),
):
    """Создать TWI-курс из утверждённой инструкции."""
    raise NotImplementedError


@router.post("/{course_id}/ai-enhance", response_model=CourseResponse)
async def ai_enhance_course(
    course_id: UUID,
    user: TokenPayload = Depends(require_roles("mentor", "park_owner", "admin")),
):
    """AI: типичные ошибки, вопросы, рекомендации по закреплению."""
    raise NotImplementedError


@router.post("/{course_id}/assign", response_model=list[CourseAssignmentResponse])
async def assign_course(
    course_id: UUID,
    body: CourseAssignRequest,
    user: TokenPayload = Depends(require_roles("mentor", "park_owner", "admin")),
):
    raise NotImplementedError


@router.get("/{course_id}/progress", response_model=list[CourseAssignmentResponse])
async def get_course_progress(course_id: UUID, user: TokenPayload = Depends(get_current_user)):
    raise NotImplementedError
