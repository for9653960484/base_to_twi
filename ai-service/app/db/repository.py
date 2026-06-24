"""Операции с БД из Celery worker."""

import json
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import text

from app.db.session import get_db_session, vector_to_pg


def update_ai_task(
    task_id: str,
    status: str,
    result_payload: dict | None = None,
    error_message: str | None = None,
    celery_task_id: str | None = None,
) -> None:
    with get_db_session() as session:
        session.execute(
            text("""
                UPDATE ai_tasks SET
                    status = :status,
                    result_payload = COALESCE(:result, result_payload),
                    error_message = :error,
                    celery_task_id = COALESCE(:celery_id, celery_task_id),
                    started_at = COALESCE(started_at, CASE WHEN :status = 'processing' THEN NOW() ELSE started_at END),
                    completed_at = CASE WHEN :status IN ('completed', 'failed', 'cancelled') THEN NOW() ELSE completed_at END
                WHERE id = :id
            """),
            {
                "id": task_id,
                "status": status,
                "result": json.dumps(result_payload) if result_payload is not None else None,
                "error": error_message,
                "celery_id": celery_task_id,
            },
        )


def update_document_ai_status(document_id: str, status: str) -> None:
    with get_db_session() as session:
        session.execute(
            text("""
                UPDATE documents SET ai_processing_status = :status, updated_at = NOW()
                WHERE id = :id
            """),
            {"id": document_id, "status": status},
        )


def delete_knowledge_chunks(source_type: str, source_id: str) -> None:
    with get_db_session() as session:
        session.execute(
            text("DELETE FROM knowledge_chunks WHERE source_type = :st AND source_id = :sid"),
            {"st": source_type, "sid": source_id},
        )


def insert_knowledge_chunks(
    equipment_id: str | None,
    source_type: str,
    source_id: str,
    chunks: list[tuple[int, str, list[float], dict]],
) -> int:
    with get_db_session() as session:
        for idx, content, embedding, metadata in chunks:
            session.execute(
                text("""
                    INSERT INTO knowledge_chunks
                        (id, equipment_id, source_type, source_id, chunk_index, content, embedding, metadata)
                    VALUES
                        (:id, :eq_id, :st::knowledge_source_type, :sid, :idx, :content, :emb::vector, :meta::jsonb)
                """),
                {
                    "id": str(uuid4()),
                    "eq_id": equipment_id,
                    "st": source_type,
                    "sid": source_id,
                    "idx": idx,
                    "content": content,
                    "emb": vector_to_pg(embedding),
                    "meta": json.dumps(metadata),
                },
            )
    return len(chunks)
