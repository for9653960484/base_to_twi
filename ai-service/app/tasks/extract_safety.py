"""Лист техники безопасности: СИЗ и условия работы из оцифрованного документа."""

import json
import logging
from uuid import uuid4

from sqlalchemy import text

from app.db.repository import update_ai_task
from app.db.session import get_db_session
from app.providers.llm_sync import complete_sync
from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Ты — инженер по охране труда промышленного оборудования.
Извлекай из технической документации средства индивидуальной защиты и условия эксплуатации.
Отвечай ТОЛЬКО валидным JSON-объектом без markdown-обёртки и без пояснений."""

USER_PROMPT = """По документу составь лист техники безопасности для работы на этом оборудовании.

Нужно извлечь только то, что явно написано в тексте. Не придумывай СИЗ и параметры.

Формат ответа:
{{
  "title": "<краткое название, например: Техника безопасности — кран RMG>",
  "ppe": [
    {{"name": "<название СИЗ>", "purpose": "<от чего защищает>", "mandatory": true}}
  ],
  "work_conditions": {{
    "temperature": "<допустимая температура или пустая строка>",
    "humidity": "<влажность или пустая строка>",
    "voltage": "<напряжение питания или пустая строка>",
    "other": [{{"name": "<параметр>", "value": "<значение>"}}]
  }},
  "notes": "<краткие обязательные условия допуска к работе или пустая строка>"
}}

В other клади прочие условия: освещённость, шум, вибрация, высота, заземление, категория помещения.
Если данных нет — верни пустые строки и пустые массивы.

Документ: {title}

Текст:
---
{text}
---"""


def _fetch_document_text(document_id: str) -> tuple[str, str, str]:
    with get_db_session() as session:
        rows = session.execute(
            text("""
                SELECT kc.content, kc.metadata, kc.equipment_id
                FROM knowledge_chunks kc
                WHERE kc.source_type = 'document'
                  AND kc.source_id = :doc_id
                ORDER BY kc.chunk_index
            """),
            {"doc_id": document_id},
        ).fetchall()

    if not rows:
        return "", "", ""

    full_text = "\n".join(row[0] for row in rows)
    metadata = rows[0][1] or {}
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except Exception:
            metadata = {}
    title = metadata.get("title", "")
    equipment_id = str(rows[0][2]) if rows[0][2] else ""
    return equipment_id, title, full_text


def _clean(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    data = json.loads(raw)
    if not isinstance(data, dict):
        return {}

    ppe = []
    for item in data.get("ppe") or []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        if not name:
            continue
        ppe.append({
            "name": name,
            "purpose": str(item.get("purpose", "")).strip(),
            "mandatory": bool(item.get("mandatory", True)),
        })

    conditions_raw = data.get("work_conditions") or {}
    if not isinstance(conditions_raw, dict):
        conditions_raw = {}
    other = []
    for item in conditions_raw.get("other") or []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        value = str(item.get("value", "")).strip()
        if name and value:
            other.append({"name": name, "value": value})

    conditions = {
        "temperature": str(conditions_raw.get("temperature", "")).strip(),
        "humidity": str(conditions_raw.get("humidity", "")).strip(),
        "voltage": str(conditions_raw.get("voltage", "")).strip(),
        "other": other,
    }
    notes = str(data.get("notes", "")).strip()
    title = str(data.get("title", "")).strip()
    return {"title": title, "ppe": ppe, "work_conditions": conditions, "notes": notes}


def _has_content(parsed: dict) -> bool:
    conditions = parsed.get("work_conditions") or {}
    return bool(parsed.get("ppe")) or bool(conditions.get("temperature")) or bool(
        conditions.get("humidity")
    ) or bool(conditions.get("voltage")) or bool(conditions.get("other")) or bool(parsed.get("notes"))


def _upsert_sheet(
    equipment_id: str,
    document_id: str,
    title: str,
    ppe: list,
    conditions: dict,
    notes: str,
    created_by: str | None,
) -> str:
    with get_db_session() as session:
        existing = session.execute(
            text("""
                SELECT id FROM safety_sheets
                WHERE equipment_id = CAST(:eq AS uuid)
                  AND source_document_id = CAST(:doc AS uuid)
                  AND status = 'draft'
                LIMIT 1
            """),
            {"eq": equipment_id, "doc": document_id},
        ).fetchone()
        payload = {
            "title": title,
            "ppe": json.dumps(ppe, ensure_ascii=False),
            "conditions": json.dumps(conditions, ensure_ascii=False),
            "notes": notes or None,
        }
        if existing:
            sheet_id = str(existing[0])
            session.execute(
                text("""
                    UPDATE safety_sheets
                    SET title = :title,
                        ppe = CAST(:ppe AS jsonb),
                        work_conditions = CAST(:conditions AS jsonb),
                        notes = :notes,
                        updated_at = NOW()
                    WHERE id = CAST(:id AS uuid)
                """),
                {**payload, "id": sheet_id},
            )
            return sheet_id

        sheet_id = str(uuid4())
        session.execute(
            text("""
                INSERT INTO safety_sheets
                    (id, equipment_id, source_document_id, title, ppe, work_conditions,
                     notes, status, created_by)
                VALUES (
                    CAST(:id AS uuid),
                    CAST(:eq AS uuid),
                    CAST(:doc AS uuid),
                    :title,
                    CAST(:ppe AS jsonb),
                    CAST(:conditions AS jsonb),
                    :notes,
                    'draft',
                    CAST(:created_by AS uuid)
                )
            """),
            {
                **payload,
                "id": sheet_id,
                "eq": equipment_id,
                "doc": document_id,
                "created_by": created_by or None,
            },
        )
        return sheet_id


@celery_app.task(
    bind=True,
    name="app.tasks.extract_safety.extract_safety_sheet",
    max_retries=2,
    default_retry_delay=30,
)
def extract_safety_sheet(
    self,
    task_id: str,
    document_id: str,
    equipment_id: str | None = None,
    created_by: str | None = None,
    **kwargs,
):
    try:
        update_ai_task(task_id, "processing", celery_task_id=self.request.id)
        kc_equipment_id, title, full_text = _fetch_document_text(document_id)
        if not full_text.strip():
            raise ValueError("Документ не проиндексирован. Сначала запустите AI-обработку документа.")

        effective_equipment_id = equipment_id or kc_equipment_id
        if not effective_equipment_id:
            raise ValueError("Не удалось определить equipment_id для документа")

        text_for_prompt = full_text[:60_000]
        raw = complete_sync(
            USER_PROMPT.format(title=title, text=text_for_prompt),
            system=SYSTEM_PROMPT,
            model_tier="heavy",
        )
        parsed = _clean(raw)
        if not _has_content(parsed):
            update_ai_task(
                task_id,
                "completed",
                result_payload={"sheets_count": 0, "warning": "СИЗ и условия работы в документе не обнаружены"},
            )
            return {"task_id": task_id, "status": "completed", "sheets_count": 0}

        sheet_title = parsed["title"] or f"Техника безопасности — {title or 'оборудование'}"
        sheet_id = _upsert_sheet(
            equipment_id=effective_equipment_id,
            document_id=document_id,
            title=sheet_title,
            ppe=parsed["ppe"],
            conditions=parsed["work_conditions"],
            notes=parsed["notes"],
            created_by=created_by,
        )
        result = {
            "sheets_count": 1,
            "safety_sheet_id": sheet_id,
            "title": sheet_title,
            "ppe_count": len(parsed["ppe"]),
        }
        update_ai_task(task_id, "completed", result_payload=result)
        return {"task_id": task_id, "status": "completed", **result}
    except Exception as exc:
        logger.exception("extract_safety failed: %s", exc)
        update_ai_task(task_id, "failed", error_message=str(exc))
        raise self.retry(exc=exc) if self.request.retries < self.max_retries else exc
