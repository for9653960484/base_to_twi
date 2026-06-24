# Dream To — Система управления базой знаний по техобслуживанию парка оборудования

Модульная платформа для управления аттракционами, технологическими картами, инструкциями ТО, TWI-курсами и матрицей компетенций технического персонала.

## Статус реализации

Легенда: ✅ реализовано и работает end-to-end · 🟡 каркас (API/UI объявлены, логика — TODO) · ⬜ не начато

| Блок | Backend | AI-service | Frontend | Примечание |
|------|---------|------------|----------|------------|
| Инфраструктура (Docker, БД, Redis) | ✅ | ✅ | ✅ | PostgreSQL 16 + pgvector, Celery worker |
| **База оборудования** | ✅ | — | ✅ | CRUD, поиск, фильтры, связи |
| **Заводская документация** | ✅ | — | ✅ | Загрузка, версии, привязка к equipment_id |
| **AI-обработка документов** | ✅ | ✅ | ✅ | Пайплайн, embeddings, статусы, polling UI |
| **Справочная система (Q&A)** | ✅ | — | ✅ | Векторный поиск + LLM-ответ |
| Технологические карты | 🟡 | 🟡 | 🟡 | Схема БД, маршруты API |
| Календарь ТО | 🟡 | — | 🟡 | Схема БД, маршруты API |
| Инструкции ТО | 🟡 | 🟡 | 🟡 | Демо-компонент шагов на UI |
| TWI-курсы | 🟡 | 🟡 | 🟡 | Схема БД, маршруты API |
| Матрица компетенций | 🟡 | 🟡 | 🟡 | Схема БД, seed уровней |
| HR-интеграция | 🟡 | — | — | Маршруты API |
| Пользователи / Auth | 🟡 | — | 🟡 | JWT, RBAC; login — TODO |
| Администрирование | — | — | 🟡 | Заглушка раздела |
| Брендбук | 🟡 | — | — | Схема БД, маршруты API |

### Отработанные блоки (подробно)

#### База оборудования (`/equipment`)

- Каталог аттракционов: название, серийное название, описание, `custom_attributes` (JSONB)
- API: список с пагинацией и поиском, создание, чтение, обновление, счётчики связей
- Роли: создание/редактирование — `admin`, `park_owner`; просмотр — все авторизованные
- UI: таблица, форма создания/редактирования, фильтр «только активные»

#### Заводская документация (`/documents`)

- Загрузка файлов (PDF, DOCX, DOC, TXT, MD) с привязкой к `equipment_id`
- Хранение по каталогу: `storage/documents/{equipment_id}/{document_id}/v{N}/`
- Версионирование: `document_versions`, история изменений
- Workflow статусов: `draft` → `pending_approval` → `published` → `archived`
- API: upload, download, список с фильтрами, новая версия, submit/approve/archive
- UI: таблица, форма загрузки, фильтр по оборудованию, скачивание

#### AI-обработка документов

Пайплайн (Celery worker, задача `document_pipeline`):

1. Извлечение текста из файла (PDF/DOCX/TXT)
2. Разбиение на chunks и векторизация (embeddings → `knowledge_chunks`)
3. LLM-анализ: регламентные работы, меры безопасности, инструменты, резюме
4. Обновление `documents.ai_processing_status` и журнала `ai_tasks`

Все модели задаются в `.env` (см. раздел [Конфигурация AI](#конфигурация-ai)).

- Запуск: кнопка «AI-обработка» в UI или `POST /api/v1/documents/{id}/ai-process`
- Статусы: `pending` → `processing` → `completed` / `failed`
- UI: авто-обновление списка при обработке, повтор при ошибке

#### Справочная система (`/knowledge`)

- Векторный поиск по проиндексированным фрагментам документов (pgvector)
- Генерация ответа через LLM с опорой на найденный контекст
- Фильтр по `equipment_id` (опционально)
- UI: поле вопроса на странице «Справка»

#### Общая инфраструктура

- **БД**: полная SQL-схема в `database/init/`, seed ролей и уровней компетенций
- **Backend**: модульный FastAPI, JWT/RBAC, dev-режим без токена (`APP_ENV=development`)
- **Frontend**: React + Vite, локализация RU/EN, React Query
- **Docker Compose**: развёртывание на сервере (postgres, redis, backend, ai-service, worker, frontend)

## Архитектура

```
dream_to/
├── database/          # Схема БД, миграции, seeds
├── backend/           # REST API, бизнес-логика, RBAC
├── ai-service/        # Микросервис AI-обработки (очереди, векторный поиск)
├── frontend/          # Веб-интерфейс (RU/EN)
├── scripts/           # setup.ps1, dev-*.ps1, init_database.py
├── requirements.txt   # Агрегатор зависимостей для локального venv
├── docs/              # Архитектурная документация
├── docker-compose.yml # Только для сервера
└── .env.example
```

### Слои системы

| Слой | Технологии | Назначение |
|------|-----------|------------|
| База данных | PostgreSQL 16 + pgvector | Хранение сущностей, JSON-атрибуты, версионирование, векторный поиск |
| Backend | Python 3.12, FastAPI, SQLAlchemy, Alembic | REST API v1, RBAC, интеграции HR/AI |
| AI Service | Celery, Redis, LLM-провайдеры | Асинхронная обработка документов, генерация инструкций/TWI |
| Frontend | React 18, Vite, TypeScript, i18next | Адаптивный UI для ролей: админ, владелец парка, наставник, техник, HR |

### Функциональные модули

- **База оборудования** — каталог аттракционов с настраиваемыми полями
- **База знаний (AI)** — заводская документация, векторный Q&A-поиск
- **Технологические карты** — регламентные работы (годовое → ежедневное ТО)
- **Календарь ТО** — сводный график на дату
- **Инструкции ТО** — шаги / ключевые моменты / причины, версионирование
- **Курсы обучения (TWI)** — генерация из утверждённых инструкций
- **Матрица компетенций** — навыки, уровни, привязка к оборудованию и сотрудникам
- **HR-интеграция** — импорт сотрудников, ролей, подразделений
- **Администрирование** — пользователи, роли, словари, интеграции

### Доменные связи

```
Оборудование ↔ Документы ↔ Инструкции ↔ TWI-курсы ↔ Компетенции ↔ Сотрудники
```

### Роли пользователей

| Роль | Доступ |
|------|--------|
| `admin` | Полный доступ, настройки системы |
| `park_owner` | Управление парком оборудования, утверждение документов |
| `mentor` | Редактирование инструкций, курсов, оценка компетенций |
| `technician` | Просмотр инструкций, прохождение курсов |
| `hr` | Импорт сотрудников, матрица компетенций (чтение/отчёты) |

## Локальная разработка (без Docker)

Основной способ разработки на рабочей машине. Подробно: **[docs/local-development.md](docs/local-development.md)**.

```powershell
# Важно: команды выполняются из КОРНЯ репозитория dream_to, не из backend/

cd C:\Users\Дима\Documents\АЛЕКСАНДР\КОДИНГ_проекты\dream_to

# 1. Настройка (venv, npm, .env)
.\setup.ps1
# или: .\scripts\setup.ps1

# 2. PostgreSQL + Redis должны быть запущены локально

# 3. Схема БД (один раз)
.\.venv\Scripts\python.exe scripts\init_database.py

# 4. Запуск (4 сервиса)
.\dev-all.ps1
# или: .\scripts\dev-all.ps1
```

| Сервис | URL |
|--------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000/docs |
| AI service | http://localhost:8001/health |
| Celery worker | отдельное окно (AI-обработка) |

Зависимости Python: корневой `requirements.txt` (агрегирует `backend/` + `ai-service/`).

## Развёртывание на сервере (Docker)

Docker Compose предназначен для **сервера**, не для ежедневной разработки.

```bash
cp .env.example .env
# Настроить продакшен-секреты и AI-ключи

docker compose up -d
```

Схема БД применяется при первом запуске `postgres` из `database/init/`.

| Сервис | Порт |
|--------|------|
| Frontend | 5173 |
| Backend | 8000 |
| AI service | 8001 |
| PostgreSQL | 5432 |
| Redis | 6379 |

## API

- **Backend**: `GET /api/v1/health` — проверка состояния
- Версионирование: `/api/v1/...`
- OpenAPI: `/docs`, `/redoc`

Основные группы endpoints:

**Реализованы:**
- `/api/v1/equipment` — оборудование (CRUD, связи)
- `/api/v1/documents` — документация (upload, download, версии, workflow, AI)
- `/api/v1/knowledge` — Q&A поиск по базе знаний
- `/api/v1/ai` — статус AI-задач, callback

**Каркас (маршруты объявлены):**
- `/api/v1/tech-cards` — технологические карты
- `/api/v1/maintenance-calendar` — календарь ТО
- `/api/v1/instructions` — инструкции ТО
- `/api/v1/courses` — TWI-курсы
- `/api/v1/competencies` — матрица компетенций
- `/api/v1/users`, `/api/v1/roles` — управление доступом
- `/api/v1/hr` — HR-интеграция
- `/api/v1/brandbook` — корпоративные шаблоны

## Конфигурация AI

Все модели задаются в `.env` (см. `.env.example`):

| Переменная | Назначение |
|------------|------------|
| `AI_PROVIDER` | `external` / `local` / `hybrid` |
| `AI_EXTERNAL_MODEL` | Тяжёлая LLM (анализ документов, Q&A) |
| `AI_LIGHT_MODEL` | Лёгкая LLM (рутинные задачи) |
| `AI_LOCAL_HEAVY_MODEL` | Локальная тяжёлая модель (Ollama) |
| `AI_LOCAL_LIGHT_MODEL` | Локальная лёгкая модель |
| `AI_EMBEDDING_MODEL` | Модель эмбеддингов (внешняя) |
| `AI_EMBEDDING_LOCAL_MODEL` | Локальная модель эмбеддингов |
| `AI_QA_MODEL` | Модель для справочной системы (пусто = `AI_EXTERNAL_MODEL`) |
| `VECTOR_DIMENSION` | Размерность векторов (1536 для OpenAI, 768 для nomic-embed-text) |

Пример для **OpenAI**:
```env
AI_PROVIDER=external
AI_EXTERNAL_API_KEY=sk-...
AI_EMBEDDING_PROVIDER=external
VECTOR_DIMENSION=1536
```

Пример для **Ollama** (on-prem):
```env
AI_PROVIDER=local
AI_LOCAL_HEAVY_MODEL=llama3.1:70b
AI_EMBEDDING_PROVIDER=local
AI_EMBEDDING_LOCAL_MODEL=nomic-embed-text
VECTOR_DIMENSION=768
```

## Документация

- [Локальная разработка](docs/local-development.md)
- [Архитектура](docs/architecture.md)
- [Модель данных](docs/data-model.md)
- [API контракты](docs/api-contracts.md)
- [AI-модуль](docs/ai-module.md)
#   d r e a m _ t o  
 