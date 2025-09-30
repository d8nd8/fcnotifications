# 🚀 Руководство по разворачиванию FC Phones на сервере

## Требования к серверу

- **ОС**: Ubuntu 20.04+ или Debian 11+
- **RAM**: Минимум 1GB, рекомендуется 2GB+
- **CPU**: 1 ядро, рекомендуется 2+
- **Диск**: Минимум 10GB свободного места
- **Сеть**: Статический IP адрес (рекомендуется)

## Вариант 1: Автоматическое разворачивание

### 1. Подготовка сервера

```bash
# Подключение к серверу
ssh root@your-server-ip

# Обновление системы
apt update && apt upgrade -y

# Установка git (если не установлен)
apt install -y git
```

### 2. Клонирование и запуск скрипта

```bash
# Клонирование репозитория
git clone https://github.com/your-username/fc_phones.git /opt/fc_phones

# Переход в директорию проекта
cd /opt/fc_phones

# Сделать скрипт исполняемым
chmod +x deploy.sh

# Запуск автоматического разворачивания
./deploy.sh
```

### 3. Настройка после разворачивания

```bash
# Редактирование переменных окружения
nano /opt/fc_phones/.env
```

Обязательно измените следующие параметры:
```env
SECRET_KEY=your-very-secure-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,your-server-ip
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_ADMIN_CHAT_ID=your-telegram-chat-id
```

### 4. Настройка домена (опционально)

```bash
# Редактирование конфигурации Nginx
nano /etc/nginx/sites-available/fc_phones
```

Замените `your-domain.com` и `your-server-ip` на ваши реальные значения.

### 5. Перезапуск сервисов

```bash
systemctl restart fc_phones_django fc_phones_bot nginx
```

## Вариант 2: Ручное разворачивание

### 1. Установка зависимостей

```bash
# Обновление системы
apt update && apt upgrade -y

# Установка необходимых пакетов
apt install -y python3 python3-pip python3-venv nginx supervisor git ufw

# Создание пользователя для приложения
useradd --system --shell /bin/bash --home-dir /opt/fc_phones --create-home fc_phones
```

### 2. Настройка проекта

```bash
# Создание директории проекта
mkdir -p /opt/fc_phones
chown fc_phones:fc_phones /opt/fc_phones

# Копирование файлов проекта в /opt/fc_phones
# (скопируйте все файлы проекта в эту директорию)

# Переход в директорию проекта
cd /opt/fc_phones

# Создание виртуального окружения
sudo -u fc_phones python3 -m venv venv

# Активация виртуального окружения
sudo -u fc_phones /opt/fc_phones/venv/bin/pip install --upgrade pip

# Установка зависимостей
sudo -u fc_phones /opt/fc_phones/venv/bin/pip install -r requirements.txt
```

### 3. Настройка переменных окружения

```bash
# Создание файла .env
cp env.example .env
nano .env
```

### 4. Настройка базы данных

```bash
# Выполнение миграций
sudo -u fc_phones /opt/fc_phones/venv/bin/python manage.py migrate

# Сбор статических файлов
sudo -u fc_phones /opt/fc_phones/venv/bin/python manage.py collectstatic --noinput

# Создание суперпользователя
sudo -u fc_phones /opt/fc_phones/venv/bin/python manage.py createsuperuser

# Создание тестового устройства
sudo -u fc_phones /opt/fc_phones/venv/bin/python manage.py create_test_device --name "Тестовое устройство"
```

### 5. Настройка systemd сервисов

#### Django сервис

```bash
nano /etc/systemd/system/fc_phones_django.service
```

Содержимое файла:
```ini
[Unit]
Description=FC Phones Django Application
After=network.target

[Service]
Type=exec
User=fc_phones
Group=fc_phones
WorkingDirectory=/opt/fc_phones
Environment=PATH=/opt/fc_phones/venv/bin
ExecStart=/opt/fc_phones/venv/bin/python /opt/fc_phones/manage.py runserver 0.0.0.0:8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

#### Telegram бот сервис

```bash
nano /etc/systemd/system/fc_phones_bot.service
```

Содержимое файла:
```ini
[Unit]
Description=FC Phones Telegram Bot
After=network.target

[Service]
Type=exec
User=fc_phones
Group=fc_phones
WorkingDirectory=/opt/fc_phones
Environment=PATH=/opt/fc_phones/venv/bin
ExecStart=/opt/fc_phones/venv/bin/python /opt/fc_phones/bot.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### 6. Настройка Nginx

```bash
nano /etc/nginx/sites-available/fc_phones
```

Содержимое файла:
```nginx
server {
    listen 80;
    server_name your-domain.com your-server-ip;

    # Логи
    access_log /var/log/nginx/fc_phones_access.log;
    error_log /var/log/nginx/fc_phones_error.log;

    # Статические файлы
    location /static/ {
        alias /opt/fc_phones/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Медиа файлы (если нужны)
    location /media/ {
        alias /opt/fc_phones/media/;
        expires 30d;
    }

    # Основное приложение
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # API документация
    location /api/docs/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 7. Активация сервисов

```bash
# Активация сайта в Nginx
ln -sf /etc/nginx/sites-available/fc_phones /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Проверка конфигурации Nginx
nginx -t

# Перезагрузка systemd
systemctl daemon-reload

# Включение и запуск сервисов
systemctl enable fc_phones_django
systemctl enable fc_phones_bot
systemctl start fc_phones_django
systemctl start fc_phones_bot
systemctl restart nginx
```

### 8. Настройка файрвола

```bash
# Настройка UFW
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
```

## Настройка SSL сертификата (Let's Encrypt)

### 1. Установка Certbot

```bash
apt install -y certbot python3-certbot-nginx
```

### 2. Получение сертификата

```bash
certbot --nginx -d your-domain.com
```

### 3. Автоматическое обновление

```bash
# Добавление в crontab
crontab -e

# Добавить строку:
0 12 * * * /usr/bin/certbot renew --quiet
```

## Мониторинг и обслуживание

### Полезные команды

```bash
# Статус сервисов
systemctl status fc_phones_django
systemctl status fc_phones_bot
systemctl status nginx

# Перезапуск сервисов
systemctl restart fc_phones_django
systemctl restart fc_phones_bot
systemctl restart nginx

# Просмотр логов
journalctl -u fc_phones_django -f
journalctl -u fc_phones_bot -f
tail -f /var/log/nginx/fc_phones_access.log
tail -f /var/log/nginx/fc_phones_error.log

# Проверка портов
netstat -tlnp | grep :8000
netstat -tlnp | grep :80
```

### Обновление приложения

```bash
# Остановка сервисов
systemctl stop fc_phones_django fc_phones_bot

# Обновление кода (если используете git)
cd /opt/fc_phones
git pull origin main

# Обновление зависимостей
sudo -u fc_phones /opt/fc_phones/venv/bin/pip install -r requirements.txt

# Выполнение миграций
sudo -u fc_phones /opt/fc_phones/venv/bin/python manage.py migrate

# Сбор статических файлов
sudo -u fc_phones /opt/fc_phones/venv/bin/python manage.py collectstatic --noinput

# Запуск сервисов
systemctl start fc_phones_django fc_phones_bot
```

## Настройка Telegram бота

### 1. Создание бота

1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Сохраните полученный токен

### 2. Получение Chat ID

1. Откройте [@userinfobot](https://t.me/userinfobot) в Telegram
2. Отправьте команду `/start`
3. Скопируйте ваш Chat ID

### 3. Настройка в .env

```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_ADMIN_CHAT_ID=123456789
```

## Проверка работоспособности

### 1. Проверка веб-интерфейса

Откройте в браузере:
- `http://your-server-ip/` - главная страница
- `http://your-server-ip/admin/` - админка
- `http://your-server-ip/api/docs/` - API документация

### 2. Проверка API

```bash
# Получение информации об устройстве
curl -H "X-TOKEN: YOUR_DEVICE_TOKEN" http://your-server-ip/api/device

# Отправка тестового сообщения
curl -X POST \
  -H "X-TOKEN: YOUR_DEVICE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sender": "Тест", "text": "Тестовое сообщение"}' \
  http://your-server-ip/api/mobile/message
```

### 3. Проверка Telegram бота

1. Найдите вашего бота в Telegram
2. Отправьте команду `/start`
3. Отправьте команду `/devices` для просмотра устройств
4. Отправьте команду `/test` для тестового уведомления

## Устранение неполадок

### Проблемы с сервисами

```bash
# Проверка статуса
systemctl status fc_phones_django --no-pager -l
systemctl status fc_phones_bot --no-pager -l

# Просмотр логов
journalctl -u fc_phones_django --since "1 hour ago"
journalctl -u fc_phones_bot --since "1 hour ago"
```

### Проблемы с Nginx

```bash
# Проверка конфигурации
nginx -t

# Просмотр логов
tail -f /var/log/nginx/error.log
tail -f /var/log/nginx/fc_phones_error.log
```

### Проблемы с базой данных

```bash
# Проверка миграций
sudo -u fc_phones /opt/fc_phones/venv/bin/python manage.py showmigrations

# Создание новых миграций
sudo -u fc_phones /opt/fc_phones/venv/bin/python manage.py makemigrations
sudo -u fc_phones /opt/fc_phones/venv/bin/python manage.py migrate
```

## Резервное копирование

### 1. Создание бэкапа

```bash
# Создание директории для бэкапов
mkdir -p /opt/backups/fc_phones

# Создание бэкапа базы данных
sudo -u fc_phones /opt/fc_phones/venv/bin/python manage.py dumpdata > /opt/backups/fc_phones/db_backup_$(date +%Y%m%d_%H%M%S).json

# Создание бэкапа файлов
tar -czf /opt/backups/fc_phones/files_backup_$(date +%Y%m%d_%H%M%S).tar.gz /opt/fc_phones --exclude=venv --exclude=__pycache__
```

### 2. Автоматическое резервное копирование

```bash
# Создание скрипта бэкапа
nano /opt/fc_phones/backup.sh
```

Содержимое скрипта:
```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/fc_phones"
DATE=$(date +%Y%m%d_%H%M%S)

# Создание директории
mkdir -p $BACKUP_DIR

# Бэкап базы данных
sudo -u fc_phones /opt/fc_phones/venv/bin/python manage.py dumpdata > $BACKUP_DIR/db_backup_$DATE.json

# Бэкап файлов
tar -czf $BACKUP_DIR/files_backup_$DATE.tar.gz /opt/fc_phones --exclude=venv --exclude=__pycache__

# Удаление старых бэкапов (старше 7 дней)
find $BACKUP_DIR -name "*.json" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

```bash
# Сделать скрипт исполняемым
chmod +x /opt/fc_phones/backup.sh

# Добавить в crontab (ежедневно в 2:00)
crontab -e
# Добавить строку:
0 2 * * * /opt/fc_phones/backup.sh
```

## Заключение

После выполнения всех шагов ваше приложение FC Phones будет полностью развернуто на сервере и готово к использованию. Не забудьте:

1. Настроить мониторинг
2. Настроить автоматические бэкапы
3. Регулярно обновлять систему и зависимости
4. Мониторить логи на предмет ошибок

При возникновении проблем проверьте логи сервисов и убедитесь, что все зависимости установлены корректно.
