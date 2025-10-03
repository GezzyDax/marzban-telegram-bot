# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Описание проекта

Telegram бот для управления доступом к VPN через Marzban панель. Бот связывает Telegram пользователей с их Marzban аккаунтами и предоставляет удобный интерфейс для проверки статуса подписки, получения subscription URL и управления пользователями (для админов).

## Основные команды разработки

### Локальная разработка

```bash
# Установка зависимостей
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Настройка окружения
cp .env.example .env
# Отредактируйте .env и укажите реальные значения

# Запуск бота локально (без Docker)
export $(cat .env | xargs)
python -m bot.main

# Запуск через Docker Compose (рекомендуется для тестирования)
docker-compose up -d

# Просмотр логов
docker-compose logs -f bot

# Остановка
docker-compose down
```

### Docker

```bash
# Сборка образа
docker build -t marzban-telegram-bot .

# Запуск контейнера (требуется PostgreSQL)
docker run -d --env-file .env marzban-telegram-bot
```

### CI/CD

**GitHub Actions** (`.github/workflows/docker-build.yml` - если существует):
- Триггеры: push в `main` или теги `v*`
- Автоматическая сборка Docker образа
- Публикация в Harbor registry (`harbor.gezzy.ru`)

**Примечание:** Если workflow файла нет, настройте его для автоматизации деплоя.

## Архитектура

### Технологический стек

- **Bot Framework**: aiogram 3.13.1 (async Telegram Bot API)
- **Database ORM**: SQLAlchemy 2.0.35 (async)
- **Database Driver**: asyncpg 0.29.0
- **HTTP Client**: aiohttp 3.10.10 (для Marzban API)
- **Configuration**: pydantic-settings 2.5.2
- **Python Version**: 3.11

### Структура модулей

```
bot/
├── main.py                 # Entry point, инициализация бота и middleware
├── config.py              # Pydantic настройки из .env
├── states.py              # FSM состояния для многошаговых диалогов
├── database/
│   ├── models.py         # SQLAlchemy модели (User, AdminLog, NotificationSettings, SentNotifications)
│   └── crud.py           # Database операции (CRUD для всех моделей)
├── services/
│   ├── marzban_api.py    # Клиент для Marzban REST API
│   └── formatters.py     # Форматирование данных для отображения
├── handlers/
│   ├── common.py         # Общие хендлеры (/start, /help)
│   ├── user.py           # Пользовательские хендлеры (подписка, ссылка, инструкция)
│   ├── user_settings.py  # Настройки уведомлений
│   ├── admin.py          # Админские хендлеры (список, статистика, логи)
│   ├── admin_fsm.py      # FSM хендлеры для добавления/поиска пользователей
│   └── simple.py         # Упрощённый роутер (legacy, объединяет все хендлеры)
├── keyboards/
│   ├── user.py           # Пользовательские клавиатуры
│   ├── user_extended.py  # Расширенные пользовательские клавиатуры
│   ├── admin.py          # Админские клавиатуры
│   ├── admin_extended.py # Расширенные админские клавиатуры
│   └── simple.py         # Базовые клавиатуры (back button, etc.)
├── middleware/
│   ├── database.py       # Инжектит AsyncSession в хендлеры через data["session"]
│   └── auth.py           # Проверяет авторизацию, инжектит data["db_user"] и data["is_admin"]
└── utils/
    ├── formatters.py     # Утилиты форматирования (прогресс-бары, даты, emoji)
    ├── exceptions.py     # Custom exceptions
    └── rate_limiter.py   # Rate limiting для Marzban API
```

### База данных

**Модели (SQLAlchemy 2.0 ORM):**

- `User`: Связь между `telegram_id` и `marzban_username`, флаг `is_admin`
- `AdminLog`: Лог действий администраторов
- `NotificationSettings`: Настройки уведомлений пользователя
- `SentNotifications`: Трек отправленных уведомлений для предотвращения дублей

**Важно:** Миграции БД управляются через Alembic (установлен), но текущая версия создает таблицы автоматически при старте (`create_tables()` в `main.py`).

**Создание таблиц:** При первом запуске бота вызывается `create_tables(engine)` которая создаёт все таблицы через `Base.metadata.create_all()`. Для продакшена рекомендуется настроить Alembic миграции.

### Marzban API Integration

Модуль `bot/services/marzban_api.py` содержит класс `MarzbanAPI` с методами:

- `get_user(username)`: Получить данные пользователя
- `list_users(offset, limit)`: Список всех пользователей
- `create_user(username, ...)`: Создать нового пользователя в Marzban
- `check_connection()`: Проверка доступности Marzban API

**Аутентификация:** Token-based (bearer token), кэширование токена на 50 минут.

### FSM (Finite State Machine)

Используется для многошаговых диалогов (хендлеры в `bot/handlers/admin_fsm.py`):

- `AddUserStates`: Добавление пользователя через RequestUser button
  - `waiting_for_user_selection` → выбор TG пользователя через shared contact button
  - `waiting_for_username` → ввод Marzban username
  - `waiting_for_confirmation` → подтверждение создания
- `SearchUserStates`: Поиск пользователя по TG ID или Marzban username
  - `waiting_for_search_query` → ввод query (telegram_id или username)

### Handler Registration

Все хендлеры регистрируются через `simple_router` в `bot/handlers/simple.py`:

```python
# В main.py
dp.include_router(simple_router)

# В bot/handlers/simple.py
simple_router = Router(name="simple")
simple_router.include_router(common_router)  # /start, /help
simple_router.include_router(user_router)    # user callbacks
simple_router.include_router(admin_router)   # admin commands/callbacks
simple_router.include_router(admin_fsm_router)  # FSM handlers
```

**Admin-only decorator:** Все админские хендлеры защищены декоратором `@admin_only` который проверяет `is_admin` из middleware.

### Middleware

Порядок выполнения middleware в `main.py`:

1. **DatabaseMiddleware** (`bot/middleware/database.py`):
   - Создает `AsyncSession` для каждого update
   - Инжектит через `data["session"]`
   - Автоматически закрывает сессию после хендлера

2. **AuthMiddleware** (`bot/middleware/auth.py`):
   - Загружает `User` из БД по `telegram_id`
   - Автосоздание initial admin пользователей из `TELEGRAM_ADMIN_IDS`
   - Инжектит `data["db_user"]` (может быть `None`) и `data["is_admin"]` (bool)

3. **MarzbanAPI Middleware** (lambda в `main.py`):
   - Инжектит готовый клиент `MarzbanAPI` через `data["marzban"]`
   - Один экземпляр на весь lifecycle бота (с кэшированием токена)

## Конфигурация (.env)

**Обязательные переменные:**

- `TELEGRAM_BOT_TOKEN`: Токен от @BotFather
- `TELEGRAM_ADMIN_IDS`: Comma-separated список Telegram ID админов (автоматически создаются при первом старте)
- `MARZBAN_API_URL`: URL Marzban панели (default: https://marzban.gezzy.ru)
- `MARZBAN_ADMIN_USERNAME`: Username админа Marzban
- `MARZBAN_ADMIN_PASSWORD`: Пароль админа Marzban
- `DATABASE_URL`: PostgreSQL connection string (формат: `postgresql+asyncpg://user:pass@host:port/db`)

**Опциональные:**

- `LOG_LEVEL`: Уровень логирования (default: INFO)
- `SUBSCRIPTION_BASE_URL`: Base URL для subscription links (default: https://marzban.gezzy.ru/sub)

## Функциональность

### Для пользователей

- **📊 Подписка**: Просмотр статуса (трафик с прогресс-баром, срок действия, status emoji)
- **🔗 Ссылка**: Получение subscription URL для импорта в VPN клиент
- **ℹ️ Инструкция**: Инструкция по подключению с кнопками скачивания клиентов (V2Box, NekoBox)
- **⚙️ Настройки**: Настройка уведомлений (о истечении, о трафике)

### Для администраторов

**Доступ через кнопку "👑 Админ-панель"** (только для `is_admin=True`):

- **➕ Добавить пользователя**:
  - Через FSM: кнопка с `RequestUser` → выбор TG контакта → ввод Marzban username
  - Через команду: `/add_user <telegram_id> <marzban_username>`
  - Автосоздание в Marzban если username не существует (unlimited data/expire)

- **🔍 Найти пользователя**: Поиск по Telegram ID или Marzban username через FSM
- **📋 Список пользователей**: Пагинация (10 на странице) с фильтром по админам
- **📊 Статистика**: Счётчики (всего, админов, обычных пользователей)
- **📋 Логи действий**: История админских операций (add_user, make_admin, etc.)

**Команды через CLI**:
- `/add_user <tg_id> <username>` - добавить пользователя
- `/remove_user <tg_id>` - удалить пользователя
- `/make_admin <tg_id>` - назначить админа
- `/revoke_admin <tg_id>` - забрать права админа

## Особенности реализации

### Архитектурные решения

**Polling vs Webhook:** Бот использует long polling (`dp.start_polling(bot)`), что упрощает development и deployment без необходимости публичного IP/домена.

**FSM Storage:** Используется `MemoryStorage()` для FSM состояний. При рестарте бота незавершённые FSM сессии будут потеряны. Для продакшена рекомендуется `RedisStorage`.

**Database Session Management:** Каждый update получает свою изолированную `AsyncSession` через middleware. Session автоматически закрывается после обработки update.

**Async Architecture:** Весь код async/await для максимальной производительности при работе с IO (Telegram API, Marzban API, Database).

### Автосоздание пользователей в Marzban

При добавлении пользователя через бота, если указанный `marzban_username` не существует в Marzban, бот автоматически создаст его с параметрами:
- `data_limit`: Unlimited
- `expire`: Unlimited
- `status`: active
- `note`: "Created via bot for TG user {telegram_id}"

### Начальные администраторы

Пользователи из `TELEGRAM_ADMIN_IDS` автоматически создаются в БД при первом обращении к боту с `is_admin=True` и `marzban_username=admin_{telegram_id}`.

### Форматирование данных

Утилиты в `bot/utils/formatters.py`:

- **Трафик**:
  - `format_bytes(bytes: int) -> str`: Конвертация байт в читаемый формат (KB/MB/GB/TB)
  - `format_progress_bar(used: int, total: int, width: int = 20) -> str`: Визуальный прогресс-бар (█ ░) с процентами

- **Даты**:
  - `format_date_relative(dt: datetime) -> str`: Относительное форматирование ("через 5 дней", "истекла 2 дня назад")

- **Статус emoji**:
  - `format_status_emoji(status, expire_dt, used_traffic, data_limit) -> str`: Возвращает 🟢 (OK) / 🟡 (Warning) / 🔴 (Error) в зависимости от:
    - Статус пользователя в Marzban
    - Оставшийся срок действия (< 7 дней = warning)
    - Использованный трафик (> 80% = warning, > 95% = error)

### Security

- **Non-root Docker**: Контейнер запускается от пользователя `botuser` (UID 1000)
- **Multi-stage build**: Минимизация размера финального образа
- **No secrets in code**: Все чувствительные данные через environment variables

## Deployment в Kubernetes

Для продакшен деплоя используется отдельный GitOps репозиторий `marzban-bot-k8s` с ArgoCD. Deployment включает:
- Bot Deployment
- PostgreSQL (managed или external)
- Sealed Secrets для хранения credentials
- Service/Ingress (если нужен webhook mode)

## Тестирование и отладка

```bash
# Проверка синтаксиса Python
python -m py_compile bot/main.py

# Проверка типов (если используется mypy)
mypy bot/

# Просмотр логов в Docker Compose
docker-compose logs -f bot

# Проверка статуса контейнеров
docker-compose ps

# Подключение к PostgreSQL для отладки
docker-compose exec postgres psql -U marzban_bot -d marzban_bot

# SQL запросы для отладки
# Посмотреть всех пользователей: SELECT * FROM users;
# Посмотреть логи админов: SELECT * FROM admin_logs ORDER BY created_at DESC LIMIT 10;
# Посмотреть настройки уведомлений: SELECT * FROM notification_settings;

# Проверка подключения к Marzban API
# Бот автоматически проверяет соединение при старте через check_connection()
# Если API недоступен, бот завершится с sys.exit(1)

# Тестирование Marzban API вручную (curl)
curl -X POST "https://marzban.gezzy.ru/api/admin/token" \
  -F "username=admin" \
  -F "password=your_password"
```

## Troubleshooting

**Бот не стартует:**
- Проверьте что все required переменные в `.env` указаны
- Проверьте доступность PostgreSQL и Marzban API
- Смотрите логи: `docker-compose logs -f bot`

**Бот не отвечает на команды:**
- Проверьте что пользователь добавлен в БД (для обычных пользователей)
- Проверьте `is_admin` флаг для админ-команд
- Проверьте логи на ошибки middleware

**Ошибки Marzban API:**
- Проверьте что `MARZBAN_API_URL` доступен
- Проверьте credentials (`MARZBAN_ADMIN_USERNAME`, `MARZBAN_ADMIN_PASSWORD`)
- Token кэшируется на 50 минут, при ошибке аутентификации будет новая попытка получения токена

## Важные моменты при разработке

**При добавлении нового хендлера:**
1. Создайте хендлер функцию в соответствующем файле (`handlers/user.py` или `handlers/admin.py`)
2. Используйте dependency injection из middleware: `session: AsyncSession`, `db_user: User | None`, `is_admin: bool`, `marzban: MarzbanAPI`
3. Для админских хендлеров добавьте `@admin_only` decorator
4. Зарегистрируйте хендлер в соответствующем роутере
5. Создайте клавиатуру в `keyboards/` если нужна

**При добавлении новой модели БД:**
1. Создайте класс в `bot/database/models.py` унаследованный от `Base`
2. Добавьте CRUD операции в `bot/database/crud.py`
3. При следующем старте бота таблица будет создана автоматически
4. Для продакшена создайте Alembic миграцию

**При работе с FSM:**
1. Определите состояния в `bot/states.py`
2. Создайте хендлеры в `bot/handlers/admin_fsm.py`
3. Используйте `state.set_state()` для перехода между состояниями
4. Очищайте состояние через `state.clear()` после завершения

**При работе с Marzban API:**
- Все методы async, используйте `await`
- Token кэшируется автоматически (50 минут)
- При ошибках выбрасывается `MarzbanAPIError`
- Всегда оборачивайте в try/except для graceful error handling
