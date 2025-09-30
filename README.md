# FC Phones - Сервис Алертов с Telegram-уведомлениями

Django REST API сервис для управления устройствами с удобными Telegram-уведомлениями в формате алертов.

## 🚀 Возможности

- **Управление устройствами**: Регистрация и аутентификация устройств по токенам
- **Отчеты о батарее**: Отслеживание уровня заряда батареи (0-100%) - используется как keep-alive
- **Сообщения**: Прием и хранение сообщений от устройств
- **Telegram-алерты**: Красивые уведомления в админ-чат при новых сообщениях
- **REST API**: Полноценный API с аутентификацией по заголовку X-TOKEN

## 📱 Формат уведомлений

Каждое новое сообщение от устройства приходит в удобном формате алерта:

```
🚨 НОВОЕ СООБЩЕНИЕ

📱 Устройство: Мой телефон
⏰ Время: 15.01.2024 14:30:25
👤 Отправитель: Иван Петров

💬 Сообщение:
Помогите! Застрял в лифте на 5 этаже!
```

## ⚡ Быстрый запуск

### 1. Автоматическая установка

```bash
./setup.sh
```

### 2. Ручная установка

```bash
# Создать виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

# Настроить окружение
cp env.example .env
# Отредактируйте .env файл с вашими настройками

# Создать базу данных
python manage.py migrate

# Создать тестовое устройство
python manage.py create_test_device --name "Мой телефон"
```

### 3. Запуск

```bash
# Активировать окружение
source venv/bin/activate

# Запустить сервер
python manage.py runserver

# В другом терминале - запустить бота
python bot.py
```

## 🔧 Настройка

### Переменные окружения (.env)

```env
# Django настройки
SECRET_KEY=ваш-секретный-ключ
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Telegram Bot настройки
TELEGRAM_BOT_TOKEN=ваш-токен-бота
TELEGRAM_ADMIN_CHAT_ID=ваш-chat-id
```

### Получение Telegram токена

1. Создайте бота через [@BotFather](https://t.me/BotFather) в Telegram
2. Получите токен бота
3. Узнайте ID вашего чата (можно через [@userinfobot](https://t.me/userinfobot))
4. Добавьте эти данные в файл `.env`

## 📡 API Endpoints

### Аутентификация

Все запросы требуют заголовок `X-TOKEN` с токеном устройства.

### 1. GET /api/device

Получить информацию об устройстве.

**Заголовки:**
```
X-TOKEN: your-device-token
```

**Ответ:**
```json
{
  "id": "12345678-1234-1234-1234-123456789abc",
  "external_id": null,
  "token": "12345678-1234-1234-1234-123456789abc",
  "name": "Мой телефон",
  "last_seen": "2024-01-15T14:30:25Z",
  "created_at": "2024-01-15T10:00:00Z"
}
```

### 2. POST /api/mobile/battery

Отправить отчет о батарее (keep-alive).

**Заголовки:**
```
X-TOKEN: your-device-token
Content-Type: application/json
```

**Тело запроса:**
```json
{
  "battery_level": 85,
  "date_created": "2024-01-15T14:30:25Z"
}
```

**Ответ:**
```json
{
  "id": "87654321-4321-4321-4321-cba987654321",
  "message": "Отчет о батарее успешно создан"
}
```

### 3. POST /api/mobile/message

Отправить сообщение (с уведомлением в Telegram).

**Заголовки:**
```
X-TOKEN: your-device-token
Content-Type: application/json
```

**Тело запроса:**
```json
{
  "date_created": "2024-01-15T14:30:25Z",
  "sender": "Иван Петров",
  "text": "Помогите! Застрял в лифте на 5 этаже!"
}
```

**Ответ:**
```json
{
  "id": "11111111-2222-3333-4444-555555555555",
  "message": "Сообщение успешно отправлено"
}
```

## 🧪 Тестирование

```bash
# Запустить тесты API
python test_api.py
```

## 📊 Модели данных

### Device (Устройство)
- `id` (UUID, PK) - Уникальный идентификатор
- `external_id` (Text, nullable) - Внешний идентификатор
- `token` (UUID, unique) - Токен для аутентификации
- `name` (CharField) - Название устройства
- `last_seen` (DateTime, nullable) - Время последней активности (keep-alive)
- `created_at` (DateTime) - Время создания

### BatteryReport (Отчет о батарее)
- `id` (UUID, PK) - Уникальный идентификатор
- `device` (FK to Device) - Ссылка на устройство
- `battery_level` (Integer) - Уровень батареи (0-100)
- `date_created` (DateTime) - Время создания отчета
- `created_at` (DateTime) - Время записи в БД

### Message (Сообщение)
- `id` (UUID, PK) - Уникальный идентификатор
- `device` (FK to Device) - Ссылка на устройство
- `date_created` (DateTime) - Время создания сообщения
- `sender` (CharField) - Отправитель
- `text` (TextField) - Текст сообщения
- `raw_payload` (JSONField) - Исходные данные запроса
- `created_at` (DateTime) - Время записи в БД

## 🤖 Telegram Bot

Бот поддерживает следующие команды:
- `/start` - Приветственное сообщение
- `/help` - Справка по командам
- `/devices` - Список всех устройств с статусом онлайн/офлайн
- `/test` - Отправка тестового уведомления

## 🛠️ Админка Django

Доступна по адресу: http://localhost:8000/admin/

Для входа создайте суперпользователя:

```bash
python manage.py createsuperuser
```

## 📋 Примеры использования

### Получение информации об устройстве

```bash
curl -H "X-TOKEN: 12345678-1234-1234-1234-123456789abc" \
     http://localhost:8000/api/device
```

### Отправка отчета о батарее (keep-alive)

```bash
curl -X POST \
     -H "X-TOKEN: 12345678-1234-1234-1234-123456789abc" \
     -H "Content-Type: application/json" \
     -d '{"battery_level": 85}' \
     http://localhost:8000/api/mobile/battery
```

### Отправка сообщения (с уведомлением в Telegram)

```bash
curl -X POST \
     -H "X-TOKEN: 12345678-1234-1234-1234-123456789abc" \
     -H "Content-Type: application/json" \
     -d '{"sender": "Иван Петров", "text": "Помогите! Застрял в лифте!"}' \
     http://localhost:8000/api/mobile/message
```

## 🔄 Принцип работы

1. **Устройство отправляет battery report** → `last_seen` обновляется (keep-alive)
2. **Устройство отправляет message** → `last_seen` обновляется + красивое уведомление в Telegram
3. **Админ видит в Telegram** все новые сообщения в удобном формате алерта
4. **В админке Django** можно отслеживать активность устройств по `last_seen`

## 🏗️ Структура проекта

```
fc_phones/
├── fc_phones/          # Основные настройки Django
├── devices/            # Приложение для работы с устройствами
│   ├── models.py       # Модели данных
│   ├── views.py        # API представления
│   ├── serializers.py  # Сериализаторы
│   ├── authentication.py # Аутентификация
│   ├── notifications.py # Telegram уведомления
│   └── management/     # Management команды
├── bot.py             # Telegram бот
├── manage.py          # Django management
└── requirements.txt   # Зависимости
```

## 📝 TODO

- [ ] Перенести отправку уведомлений в Celery для асинхронной обработки
- [ ] Добавить валидацию токенов по времени жизни
- [ ] Реализовать rate limiting для API
- [ ] Добавить логирование API запросов
- [ ] Создать API документацию с Swagger/OpenAPI
- [ ] Добавить группировку уведомлений по устройствам

## 📄 Лицензия

MIT License