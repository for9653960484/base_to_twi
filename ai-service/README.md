# Dream To AI Service

Отдельный микросервис для асинхронной AI-обработки документов.

## Структура

```
ai-service/
├── app/
│   ├── main.py           # FastAPI: POST /tasks, GET /tasks/{id}
│   ├── config.py
│   ├── worker/
│   │   └── celery_app.py
│   ├── tasks/            # Celery tasks по типам
│   ├── providers/        # LLM provider adapter (external/local/hybrid)
│   └── parsers/          # PDF, DOCX, TXT парсеры
├── requirements.txt
└── Dockerfile
```

## Типы задач

- `document_parse` — извлечение текста, chunking, embedding
- `extract_maintenance` — технологические карты из документации
- `generate_instruction` — структурированные инструкции ТО
- `generate_course` — TWI-курсы
- `generate_competencies` — матрица компетенций
- `qa_search` — Q&A по базе знаний

## Запуск

```bash
# API
uvicorn app.main:app --port 8001 --reload

# Worker
celery -A app.worker.celery_app worker --loglevel=info
```

Подробнее: [docs/ai-module.md](../docs/ai-module.md)
