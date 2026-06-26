# Windows — вспомогательные CMD-лаунчеры

Скрипты для локальной настройки PostgreSQL 16 и pgvector (запуск **от имени администратора**).

| Файл | Назначение |
|------|------------|
| `install-pgvector.cmd` | Установка расширения pgvector |
| `enable-pgvector.cmd` | Включение pgvector в БД (файлы уже установлены) |
| `setup-pgvector.cmd` | Восстановление пароля postgres + pgvector |
| `reset-postgres-password.cmd` | Сброс пароля postgres (порт 5433) |
| `fix-postgresql.cmd` | Восстановление `pg_hba.conf` и перезапуск службы |

В корне репозитория остались тонкие обёртки с теми же именами (как `dev-all.ps1`).

Логика — в `scripts/*.ps1` и `scripts/enable_pgvector.py`.
