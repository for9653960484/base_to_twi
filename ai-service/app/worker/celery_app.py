from celery import Celery

from app.config import settings

celery_app = Celery(
    "base_to_ai",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.document_pipeline",
        "app.tasks.extract_maintenance",
        "app.tasks.generate_instruction",
        "app.tasks.generate_course",
        "app.tasks.generate_competencies",
        "app.tasks.qa_search",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_retry_delay=60,
    task_max_retries=3,
)
