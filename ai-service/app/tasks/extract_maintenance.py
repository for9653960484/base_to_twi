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
- Ежедневный или сменный осмотр, проверка перед пуском, смазка по графику, еженедельное, ежемесячное, квартальное, полугодовое и годовое обслуживание — это регламенты ТО. На каждый такой период нужна отдельная карта.
- Пустой массив допустим только если в тексте нет ни одного периодического осмотра, смазки или обслуживания.

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
TYPE_ALIASES = (
    ("ежеднев", "daily"),
    ("сменн", "daily"),
    ("еженедел", "weekly"),
    ("ежемесяч", "monthly"),
    ("квартал", "quarterly"),
    ("полугод", "semi_annual"),
    ("годов", "annual"),
    ("daily", "daily"),
    ("weekly", "weekly"),
    ("monthly", "monthly"),
    ("quarterly", "quarterly"),
    ("semi_annual", "semi_annual"),
    ("annual", "annual"),
)


def _normalize_type(raw: str) -> str:
    value = raw.strip().lower().replace("-", "_").replace(" ", "_")
    if value in VALID_TYPES:
        return value
    for alias, mapped in TYPE_ALIASES:
        if alias in value:
            return mapped
    return ""

# Регламент часто стоит в конце руководства. В модель уходят фрагменты,
# где названы периоды обслуживания, а не первые 60 тысяч знаков.
PROMPT_CHAR_BUDGET = 70_000
PROMPT_HEAD_CHARS = 1_200
SCHEDULE_MARKERS = (
    "ежедневн",
    "еженедел",
    "ежемесяч",
    "ежеквартал",
    "полугодов",
    "годовое техническ",
    "годовой техническ",
    "годового техническ",
    "профилактическое техническое обслуживание",
    "технический осмотр",
    "карта смазки",
)
SCHEDULE_WEIGHTS = (
    ("ежедневн", 4),
    ("еженедел", 4),
    ("ежемесяч", 4),
    ("ежеквартал", 3),
    ("полугодов", 3),
    ("годовое техническ", 3),
    ("годовой техническ", 3),
    ("годового техническ", 3),
)


def _marker_spans(
    text: str,
    markers: tuple[str, ...],
    *,
    before: int,
    after: int,
    cluster_gap: int,
) -> list[tuple[int, int, int]]:
    low = text.lower()
    hits: list[int] = []
    for marker in markers:
        start = 0
        while True:
            idx = low.find(marker, start)
            if idx < 0:
                break
            hits.append(idx)
            start = idx + len(marker)
    if not hits:
        return []
    hits.sort()
    spans: list[tuple[int, int, int]] = []
    cluster_start = max(0, hits[0] - before)
    cluster_end = min(len(text), hits[0] + after)
    count = 1
    last = hits[0]
    for pos in hits[1:]:
        if pos - last <= cluster_gap:
            cluster_end = min(len(text), max(cluster_end, pos + after))
            count += 1
        else:
            spans.append((cluster_start, cluster_end, count))
            cluster_start = max(0, pos - before)
            cluster_end = min(len(text), pos + after)
            count = 1
        last = pos
    spans.append((cluster_start, cluster_end, count))
    return spans


def _covered_length(ranges: list[tuple[int, int]]) -> int:
    if not ranges:
        return 0
    ordered = sorted(ranges)
    total = 0
    cur_start, cur_end = ordered[0]
    for start, end in ordered[1:]:
        if start <= cur_end:
            cur_end = max(cur_end, end)
        else:
            total += cur_end - cur_start
            cur_start, cur_end = start, end
    return total + cur_end - cur_start


def _span_score(fragment: str) -> int:
    low = fragment.lower()
    return sum(weight for marker, weight in SCHEDULE_WEIGHTS if marker in low)


def select_prompt_text(full_text: str) -> str:
    """Главы с периодами ТО в начале запроса, затем короткое название документа."""
    if len(full_text) <= PROMPT_CHAR_BUDGET:
        return full_text

    spans = _marker_spans(
        full_text, SCHEDULE_MARKERS, before=400, after=18_000, cluster_gap=4_500
    )
    ranked = sorted(
        ((start, end, _span_score(full_text[start:end])) for start, end, _count in spans),
        key=lambda item: (item[2], item[0]),
        reverse=True,
    )
    chosen: list[tuple[int, int]] = []
    for start, end, score in ranked:
        if score < 3:
            continue
        if _covered_length(chosen) >= PROMPT_CHAR_BUDGET - PROMPT_HEAD_CHARS:
            break
        chosen.append((start, end))
        if _covered_length(chosen) > PROMPT_CHAR_BUDGET - PROMPT_HEAD_CHARS:
            chosen.pop()
            room = PROMPT_CHAR_BUDGET - PROMPT_HEAD_CHARS - _covered_length(chosen)
            if room > 2_000:
                chosen.append((start, min(end, start + room)))
            break

    if not chosen:
        return full_text[:PROMPT_CHAR_BUDGET]

    ordered = sorted(chosen)
    merged: list[tuple[int, int]] = []
    for start, end in ordered:
        if merged and start <= merged[-1][1] + 200:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    parts = [full_text[start:end].strip() for start, end in merged if end > start]
    head = full_text[:PROMPT_HEAD_CHARS].strip()
    if head:
        parts.append(head)
    return "\n\n[...]\n\n".join(part for part in parts if part)


def _parse_llm_response(raw: str) -> list[dict]:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    cards = json.loads(raw)
    if isinstance(cards, dict):
        for key in ("cards", "tech_cards", "items", "data"):
            if isinstance(cards.get(key), list):
                cards = cards[key]
                break
    if not isinstance(cards, list):
        return []

    result = []
    for card in cards:
        if not isinstance(card, dict):
            continue
        mt = _normalize_type(str(card.get("maintenance_type", "")))
        if not mt:
            logger.warning("Неизвестный maintenance_type: %s, пропускаем", card.get("maintenance_type"))
            continue
        title = str(card.get("title", "")).strip()
        if not title:
            continue
        items = card.get("work_items", [])
        cleaned_items = []
        for idx, wi in enumerate(items):
            if not isinstance(wi, dict):
                continue
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

        # 2. Начало документа и фрагменты с регламентом ТО.
        # Главы обслуживания часто стоят после 60 тысяч знаков.
        text_for_prompt = select_prompt_text(full_text)

        logger.info(
            "Генерация тех. карт: document_id=%s, symbols=%d из %d",
            document_id,
            len(text_for_prompt),
            len(full_text),
        )

        prompt = USER_PROMPT.format(title=title, text=text_for_prompt)

        # 3. Вызов LLM (тяжёлая модель — gpt-4o)
        raw = complete_sync(prompt, system=SYSTEM_PROMPT, model_tier="heavy")
        logger.info("Ответ модели, первые 400 знаков: %s", raw[:400].replace("\n", " "))

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
