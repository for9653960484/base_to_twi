from app.worker.celery_app import celery_app


@celery_app.task(bind=True, name="app.tasks.generate_course.generate_course")
def generate_course(self, task_id: str, instruction_id: str, **kwargs):
    """Генерация TWI-курса из утверждённой инструкции."""
    return {
        "task_id": task_id,
        "course": {
            "preparation": "",
            "typical_mistakes": [],
            "self_check_questions": [],
            "reinforcement_tips": [],
        },
        "status": "completed",
    }
