from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.security import create_access_token, get_current_user, require_roles, TokenPayload
from app.modules.users.schemas import LoginRequest, RoleResponse, TokenResponse, UserCreate, UserResponse
from app.shared.schemas import PaginatedResponse

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    # TODO: validate credentials against DB
    raise NotImplementedError


@router.get("/me", response_model=UserResponse)
async def get_me(user: TokenPayload = Depends(get_current_user)):
    raise NotImplementedError


@router.get("/", response_model=PaginatedResponse[UserResponse])
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: TokenPayload = Depends(require_roles("admin", "hr")),
):
    return PaginatedResponse(items=[], total=0, page=page, page_size=page_size, pages=0)


@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    data: UserCreate,
    user: TokenPayload = Depends(require_roles("admin")),
):
    raise NotImplementedError
