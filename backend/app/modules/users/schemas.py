from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.shared.schemas import TimestampMixin


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str = Field(..., min_length=8)
    role_code: str
    specialization_id: Optional[UUID] = None
    department_id: Optional[UUID] = None


class UserResponse(TimestampMixin):
    id: UUID
    email: str
    full_name: str
    role_code: str
    specialization_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    is_active: bool


class RoleResponse(BaseModel):
    id: UUID
    code: str
    name: dict


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
