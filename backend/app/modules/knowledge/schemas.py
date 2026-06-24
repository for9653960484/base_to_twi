from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., min_length=3)
    equipment_id: Optional[UUID] = None
    top_k: int = Field(5, ge=1, le=20)


class KnowledgeSource(BaseModel):
    source_type: str
    source_id: UUID
    title: str
    excerpt: str
    relevance_score: float


class KnowledgeSearchResponse(BaseModel):
    answer: str
    sources: list[KnowledgeSource]
    equipment_id: Optional[UUID] = None
