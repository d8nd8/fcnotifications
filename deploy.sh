#!/bin/bash

# FC Phones - Production Deployment Script
# Скрипт для разворачивания проекта на сервере

set -e  # Остановить выполнение при ошибке

echo "🚀 Начинаем разворачивание FC Phones на сервере..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Проверка, что скрипт запущен от root или с sudo
if [ "$EUID" -ne 0 ]; then
    error "Этот скрипт должен быть запущен с правами root или через sudo"
fi

# Переменные
PROJECT_NAME="fc_phones"
PROJECT_DIR="/opt/$PROJECT_NAME"
SERVICE_USER="fc_phones"
NGINX_SITES_AVAILABLE="/etc/nginx/sites-available"
NGINX_SITES_ENABLED="/etc/nginx/sites-enabled"
SYSTEMD_DIR="/etc/systemd/system"

log "Обновление системы..."
apt update && apt upgrade -y

log "Установка необходимых пакетов..."
apt install -y python3 python3-pip python3-venv nginx supervisor git ufw

log "Создание пользователя для приложения..."
if ! id "$SERVICE_USER" &>/dev/null; then
    useradd --system --shell /bin/bash --home-dir $PROJECT_DIR --create-home $SERVICE_USER
    success "Пользователь $SERVICE_USER создан"
else
    warning "Пользователь $SERVICE_USER уже существует"
fi

log "Создание директории проекта..."
mkdir -p $PROJECT_DIR
chown $SERVICE_USER:$SERVICE_USER $PROJECT_DIR

log "Клонирование репозитория (если не существует)..."
if [ ! -d "$PROJECT_DIR/.git" ]; then
    # Замените URL на ваш репозиторий
    warning "Пожалуйста, склонируйте ваш репозиторий в $PROJECT_DIR"
    warning "Или поместите файлы проекта в эту директорию"
    read -p "Нажмите Enter после размещения файлов проекта..."
fi

log "Установка зависимостей Python..."
cd $PROJECT_DIR
sudo -u $SERVICE_USER python3 -m venv venv
sudo -u $SERVICE_USER $PROJECT_DIR/venv/bin/pip install --upgrade pip
sudo -u $SERVICE_USER $PROJECT_DIR/venv/bin/pip install -r requirements.txt

log "Настройка переменных окружения..."
if [ ! -f "$PROJECT_DIR/.env" ]; then
    cp $PROJECT_DIR/env.example $PROJECT_DIR/.env
    warning "Файл .env создан из примера. Пожалуйста, отредактируйте его:"
    warning "nano $PROJECT_DIR/.env"
    warning "Обязательно измените SECRET_KEY, TELEGRAM_BOT_TOKEN и TELEGRAM_ADMIN_CHAT_ID"
    read -p "Нажмите Enter после настройки .env файла..."
fi

log "Выполнение миграций базы данных..."
sudo -u $SERVICE_USER $PROJECT_DIR/venv/bin/python $PROJECT_DIR/manage.py migrate

log "Сбор статических файлов..."
sudo -u $SERVICE_USER $PROJECT_DIR/venv/bin/python $PROJECT_DIR/manage.py collectstatic --noinput

log "Создание суперпользователя..."
warning "Создание суперпользователя Django (опционально)"
read -p "Создать суперпользователя? (y/n): " create_superuser
if [ "$create_superuser" = "y" ] || [ "$create_superuser" = "Y" ]; then
    sudo -u $SERVICE_USER $PROJECT_DIR/venv/bin/python $PROJECT_DIR/manage.py createsuperuser
fi

log "Создание тестового устройства..."
sudo -u $SERVICE_USER $PROJECT_DIR/venv/bin/python $PROJECT_DIR/manage.py create_test_device --name "Тестовое устройство"

log "Создание systemd сервиса для Django..."
cat > $SYSTEMD_DIR/fc_phones_django.service << EOF
[Unit]
Description=FC Phones Django Application
After=network.target

[Service]
Type=exec
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/manage.py runserver 0.0.0.0:8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

log "Создание systemd сервиса для Telegram бота..."
cat > $SYSTEMD_DIR/fc_phones_bot.service << EOF
[Unit]
Description=FC Phones Telegram Bot
After=network.target

[Service]
Type=exec
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/bot.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

log "Настройка Nginx..."
cat > $NGINX_SITES_AVAILABLE/$PROJECT_NAME << EOF
server {
    listen 80;
    server_name your-domain.com your-server-ip;

    # Логи
    access_log /var/log/nginx/fc_phones_access.log;
    error_log /var/log/nginx/fc_phones_error.log;

    # Статические файлы
    location /static/ {
        alias $PROJECT_DIR/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Медиа файлы (если нужны)
    location /media/ {
        alias $PROJECT_DIR/media/;
        expires 30d;
    }

    # Основное приложение
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # API документация
    location /api/docs/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Создание символической ссылки для активации сайта
ln -sf $NGINX_SITES_AVAILABLE/$PROJECT_NAME $NGINX_SITES_ENABLED/

# Удаление дефолтного сайта nginx
rm -f $NGINX_SITES_ENABLED/default

log "Проверка конфигурации Nginx..."
nginx -t

log "Перезапуск сервисов..."
systemctl daemon-reload
systemctl enable fc_phones_django
systemctl enable fc_phones_bot
systemctl start fc_phones_django
systemctl start fc_phones_bot
systemctl restart nginx

log "Настройка файрвола..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

log "Проверка статуса сервисов..."
systemctl status fc_phones_django --no-pager
systemctl status fc_phones_bot --no-pager

success "Разворачивание завершено!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Отредактируйте файл $PROJECT_DIR/.env с вашими настройками"
echo "2. Измените домен в конфигурации Nginx: $NGINX_SITES_AVAILABLE/$PROJECT_NAME"
echo "3. Настройте SSL сертификат (рекомендуется Let's Encrypt)"
echo "4. Перезапустите сервисы: systemctl restart fc_phones_django fc_phones_bot nginx"
echo ""
echo "🌐 Ваше приложение доступно по адресу: http://your-server-ip"
echo "📱 Админка: http://your-server-ip/admin/"
echo "📚 API документация: http://your-server-ip/api/docs/"
echo ""
echo "🔧 Полезные команды:"
echo "  systemctl status fc_phones_django    # Статус Django"
echo "  systemctl status fc_phones_bot       # Статус бота"
echo "  systemctl restart fc_phones_django   # Перезапуск Django"
echo "  systemctl restart fc_phones_bot      # Перезапуск бота"
echo "  journalctl -u fc_phones_django -f    # Логи Django"
echo "  journalctl -u fc_phones_bot -f       # Логи бота"
