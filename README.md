# Marzban Telegram Bot

Telegram бот для управления доступом к VPN через Marzban панель.

## Возможности

### Для администраторов:
- Добавление пользователей (привязка Telegram ID к Marzban username)
- Удаление пользователей
- Назначение/отзыв прав админа
- Просмотр списка пользователей
- Просмотр логов действий
- Статистика системы

### Для пользователей:
- Просмотр статуса подписки (трафик, срок действия)
- Получение subscription URL
- Инструкция по подключению
- Ссылки на скачивание VPN клиентов

## Быстрый старт

### Локальное тестирование

1. Создайте бота через [@BotFather](https://t.me/BotFather)

2. Скопируйте `.env.example` в `.env` и заполните:
```bash
cp .env.example .env
nano .env
```

3. Запустите с помощью Docker Compose:
```bash
docker-compose up -d
```

4. Проверьте логи:
```bash
docker-compose logs -f bot
```

### Деплой в Kubernetes

См. репозиторий `marzban-bot-k8s` для GitOps деплоя через ArgoCD.

## Команды бота

### Общие:
- `/start` - Главное меню
- `/help` - Справка

### Админские:
- `/add_user <telegram_id> <marzban_username>` - Добавить пользователя
- `/remove_user <telegram_id>` - Удалить пользователя
- `/make_admin <telegram_id>` - Назначить админа
- `/revoke_admin <telegram_id>` - Забрать права админа

## Архитектура

- **Bot**: aiogram 3.x (async Telegram Bot API)
- **Database**: PostgreSQL + SQLAlchemy 2.x
- **Marzban API**: aiohttp client
- **Deployment**: Docker + Kubernetes

## Разработка

### Установка зависимостей:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Запуск локально:
```bash
export $(cat .env | xargs)
python -m bot.main
```

## Лицензия

MIT

