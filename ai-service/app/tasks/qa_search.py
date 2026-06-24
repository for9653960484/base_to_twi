from app.worker.celery_app import celery_app


@celery_app.task(bind=True, name="app.tasks.qa_search.qa_search")
def qa_search(self, task_id: str, query: str, equipment_id: str = None, **kwargs):
    """Q&A поиск: векторный retrieval + LLM ответ."""
    return {
        "task_id": task_id,
        "answer": "",
        "sources": [],
        "status": "completed",
    }
