from app.worker.celery_app import celery_app


@celery_app.task(bind=True, name="app.tasks.generate_competencies.generate_competencies")
def generate_competencies(self, task_id: str, equipment_id: str, **kwargs):
    """Генерация компетенций и навыков на основе инструкций."""
    return {"task_id": task_id, "competencies": [], "status": "completed"}
