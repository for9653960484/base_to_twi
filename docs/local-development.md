# Локальная разработка без Docker

Пошаговая инструкция для Windows. На сервере используется [Docker Compose](../docker-compose.yml).

## Требования

| Компонент | Версия | Зачем |
|-----------|--------|-------|
| Python | 3.12+ | Backend, AI-service, worker |
| Node.js | 20+ | Frontend |
| PostgreSQL | 16 + [pgvector](https://github.com/pgvector/pgvector) | БД и векторный поиск |
| Redis | 7+ | Очередь Celery |

### PostgreSQL на Windows

1. Установите [PostgreSQL 16](https://www.postgresql.org/download/windows/).
2. Установите расширение **pgvector** — автоматически (рекомендуется):

```powershell
# PowerShell от имени администратора, из корня репозитория:
.\scripts\install_pgvector_windows.ps1 -PostgresPassword "ваш_пароль_postgres"
```

Скрипт скачает prebuilt-бинарник для PG 16.14, скопирует файлы в `C:\Program Files\PostgreSQL\16`, включит расширение и мигрирует колонку `embedding` в `vector(1536)`.

Если файлы уже скопированы вручную — только включение в БД:

```powershell
.\.venv\Scripts\python.exe scripts\enable_pgvector.py
```

Альтернатива: сборка из исходников — [pgvector Windows](https://github.com/pgvector/pgvector#windows) (нужны Visual Studio C++ Build Tools).

3. Создайте пользователя и базу (в `psql` от суперпользователя `postgres`):

```sql
CREATE USER dream_to WITH PASSWORD 'dream_to_secret';
CREATE DATABASE dream_to OWNER dream_to;
GRANT ALL PRIVILEGES ON DATABASE dream_to TO dream_to;
\c dream_to
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### Redis на Windows

- [Memurai](https://www.memurai.com/) (совместим с Redis), или
- Redis в WSL2, или
- Портативная сборка Redis для Windows.

По умолчанию: `redis://localhost:6379/0` (см. `.env`).

## Быстрый старт

```powershell
# Из корня репозитория dream_to (не из backend/)
.\scripts\setup.ps1

# Инициализация схемы (один раз)
.\.venv\Scripts\python.exe scripts\init_database.py

# Запуск всех сервисов (4 окна PowerShell)
.\scripts\dev-all.ps1
```

Или по отдельности в разных терминалах:

```powershell
.\scripts\dev-backend.ps1   # http://localhost:8000/docs
.\scripts\dev-ai.ps1        # http://localhost:8001/health
.\scripts\dev-worker.ps1    # Celery (обязателен для AI-обработки)
.\scripts\dev-frontend.ps1  # http://localhost:5173
```

## Структура окружения

- **Один venv** в корне: `.venv` (зависимости из `requirements.txt`)
- **Один `.env`** в корне — читается backend и ai-service из любой рабочей папки
- **Файлы** загружаются в `./storage` относительно корня проекта

## Переменные для локальной разработки

```env
APP_ENV=development
POSTGRES_HOST=localhost
REDIS_URL=redis://localhost:6379/0
AI_SERVICE_URL=http://localhost:8001
STORAGE_LOCAL_PATH=./storage
```

В режиме `APP_ENV=development` API не требует JWT (dev-пользователь admin).

## Полезные команды

```powershell
# Обновить зависимости Python
.\.venv\Scripts\pip.exe install -r requirements.txt

# Проверка backend
curl http://localhost:8000/health

# Проверка AI и списка моделей из .env
curl http://localhost:8001/health
```

## Linux / macOS

Аналоги скриптов `.ps1` — те же команды вручную:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/init_database.py

# Терминал 1
cd backend && uvicorn app.main:app --reload --port 8000

# Терминал 2
cd ai-service && uvicorn app.main:app --reload --port 8001

# Терминал 3
cd ai-service && celery -A app.worker.celery_app worker --loglevel=info

# Терминал 4
cd frontend && npm run dev
```

## Развёртывание на сервере (Docker)

См. раздел «Развёртывание на сервере» в [README.md](../README.md).
