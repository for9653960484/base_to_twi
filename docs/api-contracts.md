# API контракты (v1)

Базовый URL: `/api/v1`

## Общие соглашения

- Аутентификация: `Authorization: Bearer <JWT>`
- Пагинация: `?page=1&page_size=20`
- Фильтрация: query-параметры по полям
- Ошибки: `{ "detail": "...", "code": "ERROR_CODE" }`
- Локализация: `Accept-Language: ru | en`

---

## Equipment — `/equipment`

| Метод | Endpoint | Описание | Роли |
|-------|----------|----------|------|
| GET | `/` | Список с фильтрами | all |
| POST | `/` | Создать | admin, park_owner |
| GET | `/{id}` | Карточка + связи | all |
| PATCH | `/{id}` | Обновить | admin, park_owner |
| DELETE | `/{id}` | Деактивировать | admin |
| GET | `/{id}/relations` | Связи: документы, инструкции, курсы | all |

## Documents — `/documents`

| Метод | Endpoint | Описание | Роли |
|-------|----------|----------|------|
| GET | `/` | Список (?equipment_id=) | all |
| POST | `/upload` | Загрузка файла + привязка | mentor+ |
| GET | `/{id}` | Метаданные + версии | all |
| POST | `/{id}/ai-process` | Запуск AI-обработки | mentor+ |
| GET | `/{id}/ai-status` | Статус обработки | all |
| POST | `/{id}/submit` | На утверждение | mentor |
| POST | `/{id}/approve` | Утвердить | park_owner, admin |
| POST | `/{id}/archive` | В архив | park_owner, admin |

## Tech Cards — `/tech-cards`

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/` | Список (?equipment_id, ?maintenance_type) |
| GET | `/{id}` | Карточка |
| POST | `/` | Создать вручную |
| PATCH | `/{id}` | Редактировать |
| GET | `/export/{id}` | Выгрузка (корп. формат) |

## Maintenance Calendar — `/maintenance-calendar`

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/` | График (?date=YYYY-MM-DD, ?equipment_id) |
| POST | `/generate` | Пересчёт из тех. карт |

## Instructions — `/instructions`

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/` | Список |
| POST | `/` | Создать |
| GET | `/{id}` | Инструкция + шаги |
| PATCH | `/{id}` | Обновить метаданные |
| PUT | `/{id}/steps` | Обновить структуру шагов |
| POST | `/{id}/ai-generate` | AI-генерация из документов |
| POST | `/{id}/submit` | На утверждение |
| POST | `/{id}/approve` | Утвердить |
| GET | `/{id}/versions` | История версий |
| POST | `/{id}/generate-document` | Корп. шаблон (PDF/DOCX) |

## Courses — `/courses`

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/` | Список курсов |
| POST | `/` | Создать из инструкции |
| POST | `/{id}/ai-enhance` | AI: ошибки, вопросы, закрепление |
| POST | `/{id}/assign` | Назначить сотрудникам |
| GET | `/{id}/progress` | Прогресс прохождения |
| PATCH | `/assignments/{id}` | Обновить статус прохождения |

## Competencies — `/competencies`

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/matrix` | Матрица (?equipment_id, ?department_id) |
| GET | `/gaps` | Аналитика дефицита |
| POST | `/` | Создать компетенцию |
| POST | `/assess` | Оценить сотрудника |
| GET | `/reports/summary` | Отчёт |

## Knowledge — `/knowledge`

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/search` | Q&A поиск `{ "query": "...", "equipment_id": "..." }` |
| POST | `/reindex` | Переиндексация (admin) |

## Users & Roles — `/users`, `/roles`

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET/POST | `/users` | CRUD пользователей |
| GET | `/roles` | Список ролей |
| GET/POST | `/specializations` | Специализации |

## HR — `/hr`

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/sync` | Ручной импорт |
| GET | `/sync/status` | Статус последней синхронизации |
| POST | `/webhook` | Webhook от HR-системы |

## Brandbook — `/brandbook`

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/templates` | Корпоративные шаблоны |
| POST | `/templates` | Загрузить шаблон |
