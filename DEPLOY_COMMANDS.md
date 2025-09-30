# 🚀 Команды для разворачивания FC Phones на сервере

## Быстрый старт (автоматическое разворачивание)

```bash
# 1. Подключение к серверу
ssh root@your-server-ip

# 2. Клонирование проекта
git clone https://github.com/your-username/fc_phones.git /opt/fc_phones
cd /opt/fc_phones

# 3. Запуск автоматического разворачивания
chmod +x deploy.sh
./deploy.sh

# 4. Настройка переменных окружения
nano /opt/fc_phones/.env
# Измените: SECRET_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_ADMIN_CHAT_ID

# 5. Перезапуск сервисов
systemctl restart fc_phones_django fc_phones_bot nginx
```

## Ручное разворачивание

### 1. Установка зависимостей
```bash
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv nginx supervisor git ufw
useradd --system --shell /bin/bash --home-dir /opt/fc_phones --create-home fc_phones
```

### 2. Настройка проекта
```bash
mkdir -p /opt/fc_phones
chown fc_phones:fc_phones /opt/fc_phones
# Скопируйте файлы проекта в /opt/fc_phones
cd /opt/fc_phones
sudo -u fc_phones python3 -m venv venv
sudo -u fc_phones /opt/fc_phones/venv/bin/pip install --upgrade pip
sudo -u fc_phones /opt/fc_phones/venv/bin/pip install -r requirements.txt
```

### 3. Настройка окружения
```bash
cp env.example .env
nano .env  # Настройте переменные
sudo -u fc_phones /opt/fc_phones/venv/bin/python manage.py migrate
sudo -u fc_phones /opt/fc_phones/venv/bin/python manage.py collectstatic --noinput
sudo -u fc_phones /opt/fc_phones/venv/bin/python manage.py createsuperuser
sudo -u fc_phones /opt/fc_phones/venv/bin/python manage.py create_test_device --name "Тестовое устройство"
```

### 4. Настройка systemd сервисов
```bash
# Django сервис
cat > /etc/systemd/system/fc_phones_django.service << 'EOF'
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
EOF

# Telegram бот сервис
cat > /etc/systemd/system/fc_phones_bot.service << 'EOF'
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
EOF
```

### 5. Настройка Nginx
```bash
cat > /etc/nginx/sites-available/fc_phones << 'EOF'
server {
    listen 80;
    server_name your-domain.com your-server-ip;

    access_log /var/log/nginx/fc_phones_access.log;
    error_log /var/log/nginx/fc_phones_error.log;

    location /static/ {
        alias /opt/fc_phones/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/fc_phones /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
```

### 6. Запуск сервисов
```bash
systemctl daemon-reload
systemctl enable fc_phones_django fc_phones_bot
systemctl start fc_phones_django fc_phones_bot
systemctl restart nginx
ufw allow 22/tcp && ufw allow 80/tcp && ufw allow 443/tcp && ufw --force enable
```

## Полезные команды

### Управление сервисами
```bash
# Статус сервисов
systemctl status fc_phones_django fc_phones_bot nginx

# Перезапуск сервисов
systemctl restart fc_phones_django fc_phones_bot nginx

# Остановка сервисов
systemctl stop fc_phones_django fc_phones_bot

# Запуск сервисов
systemctl start fc_phones_django fc_phones_bot
```

### Просмотр логов
```bash
# Логи Django
journalctl -u fc_phones_django -f

# Логи бота
journalctl -u fc_phones_bot -f

# Логи Nginx
tail -f /var/log/nginx/fc_phones_access.log
tail -f /var/log/nginx/fc_phones_error.log
```

### Обновление приложения
```bash
systemctl stop fc_phones_django fc_phones_bot
cd /opt/fc_phones
git pull origin main
sudo -u fc_phones /opt/fc_phones/venv/bin/pip install -r requirements.txt
sudo -u fc_phones /opt/fc_phones/venv/bin/python manage.py migrate
sudo -u fc_phones /opt/fc_phones/venv/bin/python manage.py collectstatic --noinput
systemctl start fc_phones_django fc_phones_bot
```

### Резервное копирование
```bash
# Бэкап базы данных
sudo -u fc_phones /opt/fc_phones/venv/bin/python manage.py dumpdata > /opt/backups/db_backup_$(date +%Y%m%d_%H%M%S).json

# Бэкап файлов
tar -czf /opt/backups/files_backup_$(date +%Y%m%d_%H%M%S).tar.gz /opt/fc_phones --exclude=venv --exclude=__pycache__
```

### Настройка SSL (Let's Encrypt)
```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d your-domain.com
```

## Проверка работоспособности

### Веб-интерфейс
- `http://your-server-ip/` - главная страница
- `http://your-server-ip/admin/` - админка
- `http://your-server-ip/api/docs/` - API документация

### API тестирование
```bash
# Получение информации об устройстве
curl -H "X-TOKEN: YOUR_DEVICE_TOKEN" http://your-server-ip/api/device

# Отправка сообщения
curl -X POST \
  -H "X-TOKEN: YOUR_DEVICE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sender": "Тест", "text": "Тестовое сообщение"}' \
  http://your-server-ip/api/mobile/message
```

### Telegram бот
1. Найдите бота в Telegram
2. Отправьте `/start`
3. Отправьте `/devices` для просмотра устройств
4. Отправьте `/test` для тестового уведомления

## Устранение неполадок

### Проблемы с сервисами
```bash
# Проверка статуса с подробностями
systemctl status fc_phones_django --no-pager -l
systemctl status fc_phones_bot --no-pager -l

# Просмотр логов за последний час
journalctl -u fc_phones_django --since "1 hour ago"
journalctl -u fc_phones_bot --since "1 hour ago"
```

### Проблемы с Nginx
```bash
# Проверка конфигурации
nginx -t

# Просмотр логов ошибок
tail -f /var/log/nginx/error.log
```

### Проблемы с базой данных
```bash
# Проверка миграций
sudo -u fc_phones /opt/fc_phones/venv/bin/python manage.py showmigrations

# Создание новых миграций
sudo -u fc_phones /opt/fc_phones/venv/bin/python manage.py makemigrations
sudo -u fc_phones /opt/fc_phones/venv/bin/python manage.py migrate
```

## Настройка Telegram бота

1. Создайте бота через [@BotFather](https://t.me/BotFather)
2. Получите токен бота
3. Узнайте ID чата через [@userinfobot](https://t.me/userinfobot)
4. Добавьте в `.env`:
   ```env
   TELEGRAM_BOT_TOKEN=your-token-here
   TELEGRAM_ADMIN_CHAT_ID=your-chat-id-here
   ```
