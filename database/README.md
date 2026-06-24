# Dream To — Database Layer

SQL-схема, миграции и начальные данные.

## Структура

```
database/
├── init/                 # SQL для docker-entrypoint-initdb.d
│   ├── 01_schema.sql     # Полная схема
│   └── 02_seed.sql       # Роли, уровни компетенций
├── migrations/           # Alembic (используется backend)
└── README.md
```

## Применение

### Docker (автоматически)
При первом запуске `docker compose up` скрипты из `init/` выполняются автоматически.

### Alembic (через backend)
```bash
cd backend
alembic upgrade head
```

## Расширяемость

- **Настраиваемые поля**: таблица `custom_field_definitions` + JSONB `custom_attributes`
- **Версионирование**: `*_versions` + `*_version_history` для документов и инструкций
- **Векторный поиск**: `knowledge_chunks` с pgvector

Подробнее: [docs/data-model.md](../docs/data-model.md)
