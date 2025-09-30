# 🚀 Быстрый запуск FC Phones

## 1. Автоматическая установка

```bash
./setup.sh
```

## 2. Ручная установка

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

## 3. Запуск

```bash
# Активировать окружение
source venv/bin/activate

# Запустить сервер
python manage.py runserver

# В другом терминале - запустить бота
python bot.py
```

## 4. Тестирование

```bash
# Запустить тесты API
python test_api.py
```

## 5. Получить токен устройства

После создания тестового устройства, токен будет выведен в консоль. Используйте его для тестирования API.

## 6. Примеры API запросов

```bash
# Получить информацию об устройстве
curl -H "X-TOKEN: ВАШ_ТОКЕН" http://localhost:8000/api/device

# Отправить отчет о батарее (keep-alive)
curl -X POST \
  -H "X-TOKEN: ВАШ_ТОКЕН" \
  -H "Content-Type: application/json" \
  -d '{"battery_level": 85}' \
  http://localhost:8000/api/mobile/battery

# Отправить сообщение (с уведомлением в Telegram)
curl -X POST \
  -H "X-TOKEN: ВАШ_ТОКЕН" \
  -H "Content-Type: application/json" \
  -d '{"sender": "Иван Петров", "text": "Помогите! Застрял в лифте!"}' \
  http://localhost:8000/api/mobile/message
```

## 7. Настройка Telegram бота

1. Создайте бота через [@BotFather](https://t.me/BotFather) в Telegram
2. Получите токен бота
3. Узнайте ID вашего чата (можно через [@userinfobot](https://t.me/userinfobot))
4. Добавьте эти данные в файл `.env`

## 8. Админка

Доступна по адресу: http://localhost:8000/admin/

Создайте суперпользователя:
```bash
python manage.py createsuperuser
```

## 9. Формат уведомлений

Каждое новое сообщение от устройства будет приходить в удобном формате:

```
🚨 НОВОЕ СООБЩЕНИЕ

📱 Устройство: Мой телефон
⏰ Время: 15.01.2024 14:30:25
👤 Отправитель: Иван Петров

💬 Сообщение:
Помогите! Застрял в лифте на 5 этаже!
```

## 10. Команды бота

- `/start` - Приветствие и описание сервиса
- `/help` - Справка по командам
- `/devices` - Список всех устройств с статусом
- `/test` - Тестовое уведомление