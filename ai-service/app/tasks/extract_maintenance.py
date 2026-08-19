"""Извлечение технологических карт из проиндексированного документа.

Пайплайн:
1. Достать чанки документа из knowledge_chunks
2. Отправить в gpt-4o (structured output) с промптом
3. Создать черновики tech_cards в БД
4. Обновить статус задачи
"""

import json
import logging
from uuid import uuid4

from sqlalchemy import text

from app.config import settings
from app.db.repository import update_ai_task
from app.db.session import get_db_session
from app.providers.llm_sync import complete_sync
from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Промпты
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """Ты — инженер по техническому обслуживанию промышленного оборудования.
Твоя задача — извлечь из технической документации структурированные технологические карты ТО.
Отвечай ТОЛЬКО валидным JSON-массивом без markdown-обёртки и без пояснений."""

USER_PROMPT = """На основе приведённой технической документации по оборудованию сформируй список технологических карт обслуживания.

Для каждого регламента (ежедневного, еженедельного, ежемесячного и т.д.) создай отдельную карту.
Извлекай только те регламенты, которые явно упомянуты в документе.

Формат ответа — JSON-массив объектов:
[
  {{
    "maintenance_type": "<annual|semi_annual|quarterly|monthly|weekly|daily>",
    "title": "<краткое название карты, например: Ежемесячное ТО станка XYZ>",
    "work_items": [
      {{
        "order": 1,
        "description": "<подробное описание операции>",
        "tools": ["<инструмент 1>", "<инструмент 2>"],
        "safety": ["<мера безопасности>"],
        "control_params": {{}}
      }}
    ]
  }}
]

Правила:
- Включай только реально описанные работы — не придумывай операции.
- "tools" — конкретный инструмент или СИЗ, упомянутый в тексте.
- "safety" — обязательные меры безопасности для операции.
- "control_params" — словарь измеряемых параметров: {{"напряжение": "220 В"}}, или пустой объект.
- order — порядковый номер начиная с 1.
- Если документ не содержит регламентов ТО — верни пустой массив [].

Документ: {title}

Текст:
---
{text}
---"""


# ---------------------------------------------------------------------------
# Вспомогательные функции работы с БД
# ---------------------------------------------------------------------------

def _fetch_document_chunks(document_id: str) -> tuple[str, str, str]:
    """Возвращает (equipment_id, title, full_text) из knowledge_chunks."""
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


def _fetch_document_meta(document_id: str) -> tuple[str, str]:
    """Возвращает (equipment_id, title) напрямую из таблицы documents."""
    with get_db_session() as session:
        row = session.execute(
            text("SELECT equipment_id, title FROM documents WHERE id = :id"),
            {"id": document_id},
        ).fetchone()
    if not row:
        return "", ""
    return str(row[0]), row[1] or ""


def _dev_user_id() -> str:
    """Возвращает UUID dev-пользователя, если он есть в БД."""
    with get_db_session() as session:
        row = session.execute(
            text("SELECT id FROM users WHERE id = '00000000-0000-0000-0000-000000000001' LIMIT 1")
        ).fetchone()
    return "00000000-0000-0000-0000-000000000001" if row else ""


def _upsert_tech_card(
    equipment_id: str,
    document_id: str,
    maintenance_type: str,
    title: str,
    work_items: list[dict],
    created_by: str | None,
) -> str:
    """Создаёт или обновляет черновик тех. карты. Возвращает id."""
    with get_db_session() as session:
        existing = session.execute(
            text("""
                SELECT id FROM tech_cards
                WHERE equipment_id = CAST(:eq AS uuid)
                  AND maintenance_type = CAST(:mt AS maintenance_type)
                  AND source_document_id = CAST(:doc AS uuid)
                  AND status = 'draft'
                LIMIT 1
            """),
            {"eq": equipment_id, "mt": maintenance_type, "doc": document_id},
        ).fetchone()

        if existing:
            card_id = str(existing[0])
            session.execute(
                text("""
                    UPDATE tech_cards
                    SET title = :title,
                        work_items = CAST(:wi AS jsonb),
                        updated_at = NOW()
                    WHERE id = CAST(:id AS uuid)
                """),
                {"title": title, "wi": json.dumps(work_items, ensure_ascii=False), "id": card_id},
            )
            return card_id

        card_id = str(uuid4())
        session.execute(
            text("""
                INSERT INTO tech_cards
                    (id, equipment_id, maintenance_type, title, work_items,
                     status, source_document_id, created_by)
                VALUES (
                    CAST(:id AS uuid),
                    CAST(:eq AS uuid),
                    CAST(:mt AS maintenance_type),
                    :title,
                    CAST(:wi AS jsonb),
                    'draft',
                    CAST(:doc AS uuid),
                    CAST(:created_by AS uuid)
                )
            """),
            {
                "id": card_id,
                "eq": equipment_id,
                "mt": maintenance_type,
                "title": title,
                "wi": json.dumps(work_items, ensure_ascii=False),
                "doc": document_id,
                "created_by": created_by or None,
            },
        )
        return card_id


# ---------------------------------------------------------------------------
# Парсинг ответа LLM
# ---------------------------------------------------------------------------

VALID_TYPES = {"annual", "semi_annual", "quarterly", "monthly", "weekly", "daily"}


def _parse_llm_response(raw: str) -> list[dict]:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    cards = json.loads(raw)
    if not isinstance(cards, list):
        return []

    result = []
    for card in cards:
        mt = card.get("maintenance_type", "").strip()
        if mt not in VALID_TYPES:
            logger.warning("Неизвестный maintenance_type: %s, пропускаем", mt)
            continue
        title = str(card.get("title", "")).strip()
        if not title:
            continue
        items = card.get("work_items", [])
        cleaned_items = []
        for idx, wi in enumerate(items):
            cleaned_items.append({
                "order": int(wi.get("order", idx + 1)),
                "description": str(wi.get("description", "")).strip(),
                "tools": [str(t) for t in wi.get("tools", []) if t],
                "safety": [str(s) for s in wi.get("safety", []) if s],
                "control_params": wi.get("control_params", {}) if isinstance(wi.get("control_params"), dict) else {},
            })
        result.append({"maintenance_type": mt, "title": title, "work_items": cleaned_items})
    return result


# ---------------------------------------------------------------------------
# Celery task
# ---------------------------------------------------------------------------

@celery_app.task(
    bind=True,
    name="app.tasks.extract_maintenance.extract_maintenance_works",
    max_retries=2,
    default_retry_delay=30,
)
def extract_maintenance_works(
    self,
    task_id: str,
    document_id: str,
    equipment_id: str | None = None,
    created_by: str | None = None,
    **kwargs,
):
    """LLM-генерация черновиков технологических карт из проиндексированного документа."""
    try:
        update_ai_task(task_id, "processing", celery_task_id=self.request.id)

        # 1. Получаем текст из knowledge_chunks (уже проиндексированных)
        kc_equipment_id, title, full_text = _fetch_document_chunks(document_id)

        if not full_text.strip():
            # Документ ещё не проиндексирован — берём мета из documents
            kc_equipment_id, title = _fetch_document_meta(document_id)
            raise ValueError(
                "Документ не проиндексирован. Сначала запустите AI-обработку документа."
            )

        effective_equipment_id = equipment_id or kc_equipment_id
        if not effective_equipment_id:
            raise ValueError("Не удалось определить equipment_id для документа")

        # 2. Ограничиваем текст для промпта (gpt-4o: 128K токенов ≈ ~500K символов)
        # Берём первые ~60 000 символов — достаточно для большинства регламентов
        text_for_prompt = full_text[:60_000]

        logger.info(
            "Генерация тех. карт: document_id=%s, symbols=%d",
            document_id,
            len(text_for_prompt),
        )

        prompt = USER_PROMPT.format(title=title, text=text_for_prompt)

        # 3. Вызов LLM (тяжёлая модель — gpt-4o)
        raw = complete_sync(prompt, system=SYSTEM_PROMPT, model_tier="heavy")

        # 4. Парсинг ответа
        cards = _parse_llm_response(raw)
        logger.info("LLM вернул %d тех. карт", len(cards))

        if not cards:
            update_ai_task(
                task_id, "completed",
                result_payload={"tech_cards_count": 0, "tech_cards": [], "warning": "Регламенты ТО в документе не обнаружены"},
            )
            return {"task_id": task_id, "status": "completed", "tech_cards_count": 0}

        # 5. Сохраняем черновики в БД
        created_ids = []
        for card in cards:
            card_id = _upsert_tech_card(
                equipment_id=effective_equipment_id,
                document_id=document_id,
                maintenance_type=card["maintenance_type"],
                title=card["title"],
                work_items=card["work_items"],
                created_by=created_by,
            )
            created_ids.append(card_id)
            logger.info("Тех. карта сохранена: id=%s type=%s", card_id, card["maintenance_type"])

        result = {
            "tech_cards_count": len(created_ids),
            "tech_cards": [
                {"id": cid, "type": c["maintenance_type"], "title": c["title"]}
                for cid, c in zip(created_ids, cards)
            ],
        }
        update_ai_task(task_id, "completed", result_payload=result)
        return {"task_id": task_id, "status": "completed", **result}

    except Exception as exc:
        logger.exception("extract_maintenance failed: %s", exc)
        update_ai_task(task_id, "failed", error_message=str(exc))
        raise self.retry(exc=exc) if self.request.retries < self.max_retries else exc
