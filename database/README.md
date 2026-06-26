# Dream To — Database Layer

SQL-схема, миграции и начальные данные.

## Структура

```
database/
├── init/                          # Только для Docker (docker-entrypoint-initdb.d)
│   ├── 01_schema.sql              # Полная схема с pgvector
│   └── 02_seed.sql                # Роли, уровни компетенций
├── schemas/
│   └── 01_schema_no_vector.sql    # Локальная разработка без pgvector
├── migrations/                    # Alembic (каркас, версий пока нет)
└── README.md
```

> **Важно:** `01_schema_no_vector.sql` намеренно **не** лежит в `init/` — иначе Docker применит обе схемы и упадёт на дубликатах. Локально без pgvector используйте `scripts/init_database.py` (автовыбор схемы).

## Применение

### Docker (автоматически)

При первом запуске `docker compose up` выполняются только файлы из `database/init/`.

### Локально (Windows / без Docker)

```powershell
.\.venv\Scripts\python.exe scripts\init_database.py
# принудительно без pgvector:
.\.venv\Scripts\python.exe scripts\init_database.py --no-vector
```

### Alembic (через backend)

Каркас в `database/migrations/`; версионных миграций пока нет — схема задаётся SQL-файлами выше.

## Расширяемость

- **Настраиваемые поля**: `custom_field_definitions` + JSONB `custom_attributes`
- **Версионирование**: `*_versions` + `*_version_history`
- **Векторный поиск**: `knowledge_chunks` с pgvector (или `REAL[]` в no-vector схеме)

Подробнее: [docs/data-model.md](../docs/data-model.md)
