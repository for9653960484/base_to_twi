from app.worker.celery_app import celery_app

MAINTENANCE_EXTRACTION_PROMPT = """
Проанализируй техническую документацию и извлеки перечень регламентных работ.
Для каждой работы укажи: maintenance_type (annual|semi_annual|quarterly|monthly|weekly|daily),
title, work_items (order, description, tools, safety, control_params).
Верни строго JSON-массив.
"""


@celery_app.task(bind=True, name="app.tasks.extract_maintenance.extract_maintenance_works")
def extract_maintenance_works(self, task_id: str, document_id: str, equipment_id: str, **kwargs):
    """LLM-анализ: извлечение технологических карт из документации."""
    # TODO: load chunks, call LLM, parse structured JSON
    return {"task_id": task_id, "tech_cards": [], "status": "completed"}
