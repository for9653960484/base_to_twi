from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.shared.schemas import LocalizedStr


class SkillResponse(BaseModel):
    id: UUID
    code: str
    name: LocalizedStr
    description: Optional[LocalizedStr] = None


class CompetencyResponse(BaseModel):
    id: UUID
    code: str
    name: LocalizedStr
    skills: list[SkillResponse] = Field(default_factory=list)


class MatrixCell(BaseModel):
    user_id: UUID
    user_name: str
    skill_id: UUID
    skill_name: LocalizedStr
    level_value: int
    required_level: int
    gap: int  # required - actual


class CompetencyMatrix(BaseModel):
    equipment_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    cells: list[MatrixCell]


class AssessRequest(BaseModel):
    user_id: UUID
    skill_id: UUID
    level_value: int = Field(..., ge=0, le=5)
    notes: Optional[str] = None


class CompetencyGapReport(BaseModel):
    equipment_id: UUID
    equipment_name: str
    skill_name: LocalizedStr
    users_below_required: int
    average_level: float
