import json
import logging
from pathlib import Path

from app.config import settings
from app.db.repository import (
    delete_knowledge_chunks,
    insert_knowledge_chunks,
    update_ai_task,
    update_document_ai_status,
)
from app.parsers.document_parser import chunk_text, extract_text
from app.providers.embeddings import embed_texts
from app.providers.llm_sync import complete_sync
from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)

ANALYSIS_SYSTEM = """Ты — инженер по техническому обслуживанию аттракционов.
Анализируй заводскую документацию и извлекай структурированную информацию.
Отвечай ТОЛЬКО валидным JSON без markdown-обёртки."""

ANALYSIS_PROMPT = """Проанализируй фрагмент технической документации и извлеки:
1. maintenance_works — список регламентных работ с полями:
   - maintenance_type: annual|semi_annual|quarterly|monthly|weekly|daily
   - title: название
   - description: краткое описание
2. safety_notes — меры безопасности (массив строк)
3. tools — инструменты (массив строк)
4. summary — краткое резюме документа (1-2 предложения)

Текст документа:
---
{text}
---

Верни JSON: {{"maintenance_works": [], "safety_notes": [], "tools": [], "summary": ""}}"""


def _resolve_file_path(file_path: str) -> Path:
    path = Path(file_path)
    if path.is_file():
        return path
    full = Path(settings.storage_local_path_resolved) / file_path
    if full.is_file():
        return full
    raise FileNotFoundError(f"File not found: {file_path}")


@celery_app.task(bind=True, name="app.tasks.document_pipeline.process_document", max_retries=2)
def process_document(
    self,
    task_id: str,
    document_id: str,
    equipment_id: str,
    file_path: str,
    title: str = "",
    **kwargs,
):
    """Полный пайплайн: парсинг → chunking → embeddings → индексация → LLM-анализ."""
    celery_id = self.request.id
    try:
        update_ai_task(task_id, "processing", celery_task_id=celery_id)
        update_document_ai_status(document_id, "processing")

        full_path = _resolve_file_path(file_path)
        text = extract_text(str(full_path))
        if not text.strip():
            raise ValueError("Document contains no extractable text")

        chunks = chunk_text(text, chunk_size=1200, overlap=200)
        logger.info("Document %s: %d chunks", document_id, len(chunks))

        embeddings = embed_texts(chunks)
        if len(embeddings) != len(chunks):
            raise ValueError("Embedding count mismatch")

        delete_knowledge_chunks("document", document_id)

        chunk_records = [
            (
                i,
                chunk,
                emb,
                {"document_id": document_id, "title": title, "chunk_total": len(chunks)},
            )
            for i, (chunk, emb) in enumerate(zip(chunks, embeddings))
        ]
        inserted = insert_knowledge_chunks(equipment_id, "document", document_id, chunk_records)

        analysis = _analyze_document(text[:12000], title)

        result = {
            "chunks_count": inserted,
            "text_length": len(text),
            "analysis": analysis,
            "models": {
                "embedding": settings.AI_EMBEDDING_MODEL
                if settings.AI_EMBEDDING_PROVIDER != "local"
                else settings.AI_EMBEDDING_LOCAL_MODEL,
                "analysis": settings.AI_EXTERNAL_MODEL
                if settings.AI_PROVIDER != "local"
                else settings.AI_LOCAL_HEAVY_MODEL,
            },
        }

        update_ai_task(task_id, "completed", result_payload=result)
        update_document_ai_status(document_id, "completed")

        return {"task_id": task_id, "status": "completed", **result}

    except Exception as exc:
        logger.exception("Document pipeline failed: %s", exc)
        update_ai_task(task_id, "failed", error_message=str(exc))
        update_document_ai_status(document_id, "failed")
        raise


def _analyze_document(text: str, title: str) -> dict:
    try:
        prompt = ANALYSIS_PROMPT.format(text=text)
        if title:
            prompt = f"Документ: {title}\n\n" + prompt

        raw = complete_sync(prompt, system=ANALYSIS_SYSTEM, model_tier="heavy")
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        return json.loads(raw)
    except Exception as exc:
        logger.warning("LLM analysis failed, returning empty: %s", exc)
        return {
            "maintenance_works": [],
            "safety_notes": [],
            "tools": [],
            "summary": "",
            "analysis_error": str(exc),
        }
