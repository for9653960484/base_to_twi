# Dream To Backend

FastAPI REST API v1 с модульной доменной архитектурой.

## Структура

```
backend/
├── app/
│   ├── main.py              # Точка входа
│   ├── api/v1/router.py     # Агрегатор маршрутов
│   ├── core/                # Config, DB, security, exceptions
│   ├── shared/              # Общие схемы, утилиты
│   └── modules/             # Доменные модули
│       ├── equipment/
│       ├── documents/
│       ├── tech_cards/
│       ├── maintenance_calendar/
│       ├── instructions/
│       ├── twi_courses/
│       ├── competencies/
│       ├── users/
│       ├── hr/
│       ├── knowledge/
│       ├── brandbook/
│       └── ai_processing/
├── scripts/
├── alembic/
├── requirements.txt
└── Dockerfile
```

Каждый модуль содержит:
- `router.py` — HTTP endpoints
- `schemas.py` — Pydantic DTO
- `service.py` — бизнес-логика (TODO)
- `models.py` — SQLAlchemy модели (TODO)

## Запуск

Локальная разработка — из **корня репозитория** (`dream_to/`), см. [docs/local-development.md](../docs/local-development.md).

```powershell
cd ..   # из backend/ в корень
.\setup.ps1
.\scripts\dev-backend.ps1
```

API docs: http://localhost:8000/docs
