from typing import Any

from app.worker.celery_app import celery_app


TASK_MAP = {
    "document_pipeline": "app.tasks.document_pipeline.process_document",
    "document_parse": "app.tasks.document_pipeline.process_document",
    "extract_maintenance": "app.tasks.extract_maintenance.extract_maintenance_works",
    "generate_instruction": "app.tasks.generate_instruction.generate_instruction",
    "generate_course": "app.tasks.generate_course.generate_course",
    "generate_competencies": "app.tasks.generate_competencies.generate_competencies",
    "qa_search": "app.tasks.qa_search.qa_search",
    "reindex": "app.tasks.document_pipeline.process_document",
}


def dispatch_task(
    task_type: str,
    equipment_id: str | None = None,
    source_type: str | None = None,
    source_id: str | None = None,
    input_payload: dict[str, Any] | None = None,
) -> dict[str, str]:
    if task_type not in TASK_MAP:
        raise ValueError(f"Unknown task type: {task_type}")

    payload = dict(input_payload or {})
    task_id = payload.pop("ai_task_id", None) or payload.pop("task_id", None)
    if not task_id:
        from uuid import uuid4
        task_id = str(uuid4())

    kwargs = {
        "task_id": task_id,
        "equipment_id": equipment_id,
        "source_type": source_type,
        "source_id": source_id,
        **payload,
    }

    async_result = celery_app.send_task(TASK_MAP[task_type], kwargs=kwargs)
    return {
        "task_id": task_id,
        "celery_task_id": async_result.id,
        "status": "pending",
    }
