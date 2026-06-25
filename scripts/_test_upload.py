import asyncio
from uuid import UUID

import app.models  # noqa: F401
from app.core.database import async_session_factory
from app.modules.documents.service import DocumentService
from app.shared.storage import FileStorage


class FakeUpload:
    def __init__(self, name: str, content: bytes, content_type: str = "text/plain"):
        self.filename = name
        self.content_type = content_type
        self._content = content

    async def read(self):
        return self._content


async def main() -> None:
    eq_id = UUID("c9b05f54-f06f-4b7c-b980-8e61051bc099")
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    f = FakeUpload("test.txt", b"hello")
    async with async_session_factory() as db:
        svc = DocumentService(db, FileStorage())
        r = await svc.upload(eq_id, "Test", f, "desc", user_id)
        await db.commit()
        print("OK", r.id, r.title)


asyncio.run(main())
