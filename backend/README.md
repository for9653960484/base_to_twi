# Dream To Backend

FastAPI REST API v1 с модульной доменной архитектурой.

## Структура

```
backend/
├── app/
│   ├── main.py              # Точка входа
│   ├── api/v1/router.py     # Агрегатор маршрутов
│   ├── core/                # Config, DB, security, exceptions
│   ├── models/              # SQLAlchemy-модели
│   ├── shared/              # Общие схемы, storage, brandbook export
│   └── modules/             # Доменные модули
│       ├── equipment/       # ✅ CRUD
│       ├── documents/       # ✅ upload, versions, AI trigger
│       ├── tech_cards/      # ✅ list, CRUD, PDF/DOCX export
│       ├── knowledge/       # ✅ Q&A поиск
│       ├── ai_processing/   # ✅ статус задач, callback
│       ├── maintenance_calendar/  # 🟡 заглушки
│       ├── instructions/    # 🟡 заглушки
│       ├── twi_courses/     # 🟡 заглушки
│       ├── competencies/    # 🟡 заглушки
│       ├── users/           # 🟡 заглушки (dev: JWT bypass)
│       ├── hr/              # 🟡 заглушки
│       └── brandbook/       # 🟡 заглушки (экспорт через tech_cards)
├── alembic/
├── requirements.txt
└── Dockerfile
```

Каждый модуль обычно содержит `router.py`, `schemas.py` и при необходимости `service.py`.

## Запуск

Локальная разработка — из **корня репозитория** (`dream_to/`), см. [docs/local-development.md](../docs/local-development.md).

```powershell
cd ..   # из backend/ в корень
.\setup.ps1
.\scripts\dev-backend.ps1
```

API docs: http://localhost:8000/docs
