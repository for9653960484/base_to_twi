from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.redis_health import redis_available
from app.tasks.dispatcher import dispatch_task


class TaskCreateRequest(BaseModel):
    task_type: str
    equipment_id: str | None = None
    source_type: str | None = None
    source_id: str | None = None
    input_payload: dict[str, Any] = Field(default_factory=dict)


class TaskResponse(BaseModel):
    task_id: str
    celery_task_id: str
    status: str = "pending"


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Base To AI Service",
    version="0.1.0",
    description="Микросервис AI-обработки документов и генерации контента",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    redis_ok = redis_available()
    return {
        "status": "ok" if redis_ok else "degraded",
        "service": "ai-service",
        "redis": "ok" if redis_ok else "unavailable",
        "provider": settings.AI_PROVIDER,
        "models": {
            "external_heavy": settings.AI_EXTERNAL_MODEL,
            "external_light": settings.AI_LIGHT_MODEL,
            "local_heavy": settings.AI_LOCAL_HEAVY_MODEL,
            "local_light": settings.AI_LOCAL_LIGHT_MODEL,
            "embedding": settings.AI_EMBEDDING_MODEL
            if settings.AI_EMBEDDING_PROVIDER != "local"
            else settings.AI_EMBEDDING_LOCAL_MODEL,
            "qa": settings.qa_model,
        },
    }


@app.post("/tasks", response_model=TaskResponse, status_code=202)
async def create_task(body: TaskCreateRequest):
    """Постановка задачи в очередь Celery."""
    if not redis_available():
        raise HTTPException(
            status_code=503,
            detail="Redis unavailable. Start Redis on localhost:6379 (see docs/local-development.md).",
        )
    result = dispatch_task(
        task_type=body.task_type,
        equipment_id=body.equipment_id,
        source_type=body.source_type,
        source_id=body.source_id,
        input_payload=body.input_payload,
    )
    return TaskResponse(**result)


@app.get("/tasks/{celery_task_id}")
async def get_task_status(celery_task_id: str):
    from app.worker.celery_app import celery_app

    result = celery_app.AsyncResult(celery_task_id)
    return {
        "celery_task_id": celery_task_id,
        "status": result.status,
        "result": result.result if result.ready() else None,
    }
