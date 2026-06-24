import re
from pathlib import Path
from uuid import UUID

import aiofiles
from fastapi import UploadFile

from app.core.config import settings

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".md"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/plain",
    "text/markdown",
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


def _sanitize_filename(name: str) -> str:
    name = Path(name).name
    name = re.sub(r"[^\w.\-() ]", "_", name, flags=re.UNICODE)
    return name or "document"


class FileStorage:
    def __init__(self, base_path: str | None = None):
        self.base_path = Path(base_path or settings.storage_local_path_resolved)

    def document_dir(self, equipment_id: UUID, document_id: UUID, version: int) -> Path:
        return self.base_path / "documents" / str(equipment_id) / str(document_id) / f"v{version}"

    async def save_upload(
        self,
        file: UploadFile,
        equipment_id: UUID,
        document_id: UUID,
        version: int,
    ) -> tuple[str, int, str]:
        """Сохранить файл. Возвращает (relative_path, size, mime_type)."""
        if not file.filename:
            raise ValueError("Filename is required")

        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {ext}")

        content = await file.read()
        size = len(content)
        if size > MAX_FILE_SIZE:
            raise ValueError(f"File too large (max {MAX_FILE_SIZE // 1024 // 1024} MB)")

        mime_type = file.content_type or "application/octet-stream"
        if mime_type not in ALLOWED_MIME_TYPES and ext != ".doc":
            mime_type = {
                ".pdf": "application/pdf",
                ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                ".txt": "text/plain",
                ".md": "text/markdown",
            }.get(ext, mime_type)

        dest_dir = self.document_dir(equipment_id, document_id, version)
        dest_dir.mkdir(parents=True, exist_ok=True)

        safe_name = _sanitize_filename(file.filename)
        dest_path = dest_dir / safe_name

        async with aiofiles.open(dest_path, "wb") as f:
            await f.write(content)

        relative = str(dest_path.relative_to(self.base_path)).replace("\\", "/")
        return relative, size, mime_type

    def resolve_path(self, relative_path: str) -> Path:
        full = (self.base_path / relative_path).resolve()
        if not str(full).startswith(str(self.base_path.resolve())):
            raise ValueError("Invalid file path")
        return full

    def exists(self, relative_path: str) -> bool:
        return self.resolve_path(relative_path).is_file()


def get_storage() -> FileStorage:
    return FileStorage()
