from uuid import UUID

from pydantic import BaseModel


class BrandbookTemplateResponse(BaseModel):
    id: UUID
    title: str
    template_type: str
    file_path: str
    version: int
    is_active: bool
