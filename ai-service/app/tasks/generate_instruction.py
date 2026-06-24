from app.worker.celery_app import celery_app

INSTRUCTION_GENERATION_PROMPT = """
На основе технологической карты сформируй структурированную инструкцию ТО.
Для каждого шага укажи: step_number, title, description, key_points[], reasons[],
tools[], safety_notes, control_params.
Верни строго JSON.
"""


@celery_app.task(bind=True, name="app.tasks.generate_instruction.generate_instruction")
def generate_instruction(self, task_id: str, tech_card_id: str = None, document_id: str = None, **kwargs):
    """Генерация инструкции: шаги, ключевые моменты, причины."""
    return {"task_id": task_id, "instruction": {"steps": []}, "status": "completed"}
