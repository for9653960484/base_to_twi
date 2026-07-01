# Base To Frontend

Адаптивное веб-приложение (ПК/планшет) с локализацией RU/EN.

## Структура

```
frontend/src/
├── api/                  # HTTP-клиент и API-методы
├── components/
│   ├── layout/           # AppLayout, Sidebar, Header
│   └── ui/               # StatusBadge, PageHeader, ...
├── modules/              # Страницы по разделам
│   ├── equipment/
│   ├── documents/
│   ├── tech-cards/
│   ├── instructions/
│   ├── courses/
│   ├── competencies/
│   ├── knowledge/
│   ├── admin/
│   └── auth/
├── locales/              # ru.json, en.json
├── types/                # TypeScript типы (согласованы с backend DTO)
└── styles/               # Глобальные стили
```

## Разделы интерфейса

| Маршрут | Раздел |
|---------|--------|
| `/equipment` | База оборудования |
| `/documents` | Заводская документация |
| `/tech-cards` | Технологические карты |
| `/instructions` | Инструкции ТО (шаги/моменты/причины) |
| `/courses` | TWI-курсы |
| `/competencies` | Матрица компетенций |
| `/knowledge` | Q&A справочная система |
| `/admin` | Администрирование |

## Запуск

```bash
npm install
npm run dev
```

http://localhost:5173

## Локализация

Переключение RU/EN в шапке. Файлы переводов: `src/locales/`.
