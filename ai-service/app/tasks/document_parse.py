from app.worker.celery_app import celery_app


@celery_app.task(bind=True, name="app.tasks.document_parse.parse_document")
def parse_document(self, task_id: str, file_path: str, equipment_id: str, **kwargs):
    """Извлечение текста и chunking для векторной БЗ."""
    from app.parsers.document_parser import chunk_text, extract_text

    text = extract_text(file_path)
    chunks = chunk_text(text)
    # TODO: generate embeddings, save to knowledge_chunks
    return {"task_id": task_id, "chunks_count": len(chunks), "status": "completed"}


@celery_app.task(bind=True, name="app.tasks.document_parse.reindex_source")
def reindex_source(self, task_id: str, source_type: str, source_id: str, **kwargs):
    return {"task_id": task_id, "status": "completed"}
