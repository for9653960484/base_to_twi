from typing import Any
from uuid import UUID

import httpx

from app.core.config import settings
from app.core.exceptions import AppException


class AIServiceClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or settings.AI_SERVICE_URL).rstrip("/")

    async def dispatch_document_pipeline(
        self,
        ai_task_id: str,
        document_id: str,
        equipment_id: str,
        file_path: str,
        title: str = "",
    ) -> dict[str, Any]:
        payload = {
            "task_type": "document_pipeline",
            "equipment_id": equipment_id,
            "source_type": "document",
            "source_id": document_id,
            "input_payload": {
                "ai_task_id": ai_task_id,
                "document_id": document_id,
                "file_path": file_path,
                "title": title,
            },
        }
        return await self._post_task(payload)

    async def get_celery_status(self, celery_task_id: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.base_url}/tasks/{celery_task_id}")
            response.raise_for_status()
            return response.json()

    async def _post_task(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(f"{self.base_url}/tasks", json=payload)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as exc:
            raise AppException(
                f"AI service unavailable: {exc}",
                "AI_SERVICE_ERROR",
                status_code=503,
            ) from exc


def get_ai_client() -> AIServiceClient:
    return AIServiceClient()
