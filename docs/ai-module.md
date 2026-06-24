# AI-модуль

## Архитектура

AI-обработка вынесена в отдельный микросервис `ai-service` с асинхронными очередями Celery + Redis.

```
Backend API  --POST /tasks-->  AI Service API
                                    |
                                    v
                              Celery Queue
                                    |
                    +---------------+---------------+
                    v               v               v
              Parse Doc      LLM Analysis      Embed Chunks
                    |               |               |
                    v               v               v
              Structured       Tech Cards /     pgvector
               JSON            Instructions
```

## Типы задач

| task_type | Вход | Выход |
|-----------|------|-------|
| `document_parse` | file_path, equipment_id | chunks[], metadata |
| `extract_maintenance` | document_id, chunks | tech_cards[] |
| `generate_instruction` | tech_card_id / document_id | instruction{steps, key_points, reasons} |
| `generate_course` | instruction_id | course{blocks} |
| `generate_competencies` | equipment_id, instructions[] | competencies[], skills[] |
| `qa_search` | query, equipment_id? | answer, sources[] |
| `reindex` | source_type, source_id | chunk_count |

## Провайдеры LLM

Конфигурация через `AI_PROVIDER`:

- **external** — OpenAI-совместимый API (GPT-4o, Claude и т.д.)
- **local** — Ollama / vLLM / локальный сервер
- **hybrid** — тяжёлые задачи → external, рутинные → local/light

### Рекомендуемые модели

| Задача | Модель |
|--------|--------|
| Анализ документации, генерация инструкций | GPT-4o / Claude 3.5 / Llama 3.1 70B |
| Рутинные тексты, подсказки | GPT-4o-mini / Llama 3 8B / Qwen 2 7B |

## Структура результата AI-анализа

### Технологическая карта
```json
{
  "maintenance_type": "monthly",
  "title": "Ежемесячное ТО механизма",
  "work_items": [
    {
      "order": 1,
      "description": "Проверить натяжение цепи",
      "tools": ["ключ 19"],
      "safety": ["Отключить питание"],
      "control_params": {"tension": "15-20 мм"}
    }
  ]
}
```

### Инструкция
```json
{
  "title": "...",
  "steps": [
    {
      "step_number": 1,
      "title": "Подготовка",
      "description": "...",
      "key_points": ["Проверить блокировку"],
      "reasons": ["Предотвращение травм"],
      "tools": [],
      "safety_notes": "...",
      "media_refs": []
    }
  ]
}
```

### TWI-курс
```json
{
  "preparation": "...",
  "typical_mistakes": ["..."],
  "self_check_questions": ["..."],
  "reinforcement_tips": ["..."]
}
```

## Очереди и надёжность

- Retry: 3 попытки с exponential backoff
- Dead letter queue для failed tasks
- Webhook/callback в backend при завершении
- Статусы задач в таблице `ai_tasks`

## Безопасность

- Документы не покидают периметр при `AI_PROVIDER=local`
- API-ключи только через env/secrets
- Логирование без содержимого документов
