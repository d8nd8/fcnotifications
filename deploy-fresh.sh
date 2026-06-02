#!/bin/bash
#
# FC Phones — деплой на чистый VPS (только IP, без домена)
#
# Использование (из папки проекта, где лежит manage.py):
#   cd /opt/fc_phones/fcnotifications
#   sudo ./deploy-fresh.sh --ip 203.0.113.10
#
#   sudo ./deploy-fresh.sh --ip 203.0.113.10 \
#       --telegram-token "123:ABC" \
#       --telegram-chat-id "6513088849" \
#       --admin-user admin \
#       --admin-password "StrongPass123"
#
# Опции:
#   --ip                  Публичный IP сервера (обязательно)
#   --project-dir         Путь к проекту (по умолчанию: папка со скриптом)
#   --git-repo            URL git-репозитория (если manage.py ещё нет)
#   --telegram-token      TELEGRAM_BOT_TOKEN
#   --telegram-chat-id    TELEGRAM_ADMIN_CHAT_ID
#   --admin-user          Логин Django admin (по умолчанию: admin)
#   --admin-password      Пароль Django admin (если не указан — спросит)
#   --skip-test-device    Не создавать тестовое устройство
#   --skip-bot-tokens     Не генерировать токены для Telegram-бота
#   --skip-firewall       Не включать UFW (если SSH на нестандартном порту)
#

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log()   { echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $*"; }
ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
fail()  { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SERVER_IP=""
PROJECT_DIR=""
GIT_REPO=""
TELEGRAM_TOKEN=""
TELEGRAM_CHAT_ID=""
ADMIN_USER="admin"
ADMIN_PASSWORD=""
SKIP_TEST_DEVICE=false
SKIP_BOT_TOKENS=false
SKIP_FIREWALL=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --ip)                 SERVER_IP="$2"; shift 2 ;;
        --project-dir)        PROJECT_DIR="$2"; shift 2 ;;
        --git-repo)           GIT_REPO="$2"; shift 2 ;;
        --telegram-token)     TELEGRAM_TOKEN="$2"; shift 2 ;;
        --telegram-chat-id)   TELEGRAM_CHAT_ID="$2"; shift 2 ;;
        --admin-user)         ADMIN_USER="$2"; shift 2 ;;
        --admin-password)     ADMIN_PASSWORD="$2"; shift 2 ;;
        --skip-test-device)   SKIP_TEST_DEVICE=true; shift ;;
        --skip-bot-tokens)    SKIP_BOT_TOKENS=true; shift ;;
        --skip-firewall)      SKIP_FIREWALL=true; shift ;;
        -h|--help)
            sed -n '2,22p' "$0"
            exit 0
            ;;
        *) fail "Неизвестный аргумент: $1" ;;
    esac
done

if [[ -z "$PROJECT_DIR" ]]; then
    if [[ -f "$SCRIPT_DIR/manage.py" ]]; then
        PROJECT_DIR="$SCRIPT_DIR"
    else
        PROJECT_DIR="/opt/fc_phones"
    fi
fi

[[ "$EUID" -eq 0 ]] || fail "Запускайте от root: sudo $0 --ip YOUR_IP"

if [[ -z "$SERVER_IP" ]]; then
    read -rp "Введите публичный IP сервера: " SERVER_IP
fi
[[ "$SERVER_IP" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] || fail "Некорректный IP: $SERVER_IP"

PROJECT_NAME="fc_phones"
SERVICE_USER="fc_phones"
VENV="$PROJECT_DIR/venv"
GUNICORN_WORKERS=3

log "=== FC Phones: деплой на $SERVER_IP ==="
log "Директория проекта: $PROJECT_DIR"

log "Обновление системы..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get upgrade -y -qq

log "Установка пакетов..."
apt-get install -y -qq \
    python3 python3-venv python3-dev \
    nginx git ufw curl \
    build-essential libffi-dev

log "Создание пользователя $SERVICE_USER..."
if ! id "$SERVICE_USER" &>/dev/null; then
    useradd --system --shell /bin/bash --home-dir "$PROJECT_DIR" --create-home "$SERVICE_USER"
    ok "Пользователь создан"
else
    warn "Пользователь уже существует"
fi

log "Подготовка директории проекта..."
mkdir -p "$PROJECT_DIR"

if [[ -f "$PROJECT_DIR/manage.py" ]]; then
    ok "Проект найден в $PROJECT_DIR"
elif [[ -n "$GIT_REPO" ]]; then
    log "Клонирование $GIT_REPO ..."
    if [[ -d "$PROJECT_DIR/.git" ]]; then
        sudo -u "$SERVICE_USER" git -C "$PROJECT_DIR" pull
    elif [[ -z "$(ls -A "$PROJECT_DIR" 2>/dev/null)" ]]; then
        sudo -u "$SERVICE_USER" git clone "$GIT_REPO" "$PROJECT_DIR"
    else
        fail "Директория $PROJECT_DIR не пуста и manage.py не найден"
    fi
else
    fail "manage.py не найден в $PROJECT_DIR. Склонируйте репозиторий или укажите --git-repo"
fi

[[ -f "$PROJECT_DIR/manage.py" ]] || fail "manage.py не найден — проверьте PROJECT_DIR"

chown -R "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR"
ok "Права на проект: $SERVICE_USER"

log "Python venv и зависимости..."
if [[ ! -d "$VENV" ]]; then
    sudo -u "$SERVICE_USER" python3 -m venv "$VENV"
fi
sudo -u "$SERVICE_USER" "$VENV/bin/pip" install --upgrade pip setuptools wheel -q
sudo -u "$SERVICE_USER" "$VENV/bin/pip" install -r "$PROJECT_DIR/requirements.txt" -q
sudo -u "$SERVICE_USER" "$VENV/bin/pip" install gunicorn -q

if [[ -z "$TELEGRAM_TOKEN" ]]; then
    read -rp "TELEGRAM_BOT_TOKEN: " TELEGRAM_TOKEN
fi
if [[ -z "$TELEGRAM_CHAT_ID" ]]; then
    read -rp "TELEGRAM_ADMIN_CHAT_ID: " TELEGRAM_CHAT_ID
fi
[[ -n "$TELEGRAM_TOKEN" ]] || fail "TELEGRAM_BOT_TOKEN обязателен"
[[ -n "$TELEGRAM_CHAT_ID" ]] || fail "TELEGRAM_ADMIN_CHAT_ID обязателен"

log "Генерация SECRET_KEY..."
SECRET_KEY=$("$VENV/bin/python" -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")

log "Создание .env..."
cat > "$PROJECT_DIR/.env" <<EOF
SECRET_KEY=${SECRET_KEY}
DEBUG=False
ALLOWED_HOSTS=${SERVER_IP},127.0.0.1,localhost

TELEGRAM_BOT_TOKEN=${TELEGRAM_TOKEN}
TELEGRAM_ADMIN_CHAT_ID=${TELEGRAM_CHAT_ID}
EOF
chown "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/.env"
chmod 600 "$PROJECT_DIR/.env"
ok ".env создан"

log "Миграции и статика..."
sudo -u "$SERVICE_USER" bash -c "cd '$PROJECT_DIR' && '$VENV/bin/python' manage.py migrate --noinput"
sudo -u "$SERVICE_USER" bash -c "cd '$PROJECT_DIR' && '$VENV/bin/python' manage.py collectstatic --noinput"

mkdir -p "$PROJECT_DIR/media" "$PROJECT_DIR/staticfiles"
chown -R "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/media" "$PROJECT_DIR/staticfiles"

if [[ -z "$ADMIN_PASSWORD" ]]; then
    read -rsp "Пароль Django admin ($ADMIN_USER): " ADMIN_PASSWORD
    echo
fi
[[ -n "$ADMIN_PASSWORD" ]] || fail "Пароль admin обязателен"

log "Создание суперпользователя..."
sudo -u "$SERVICE_USER" bash -c "
cd '$PROJECT_DIR'
DJANGO_SUPERUSER_USERNAME='$ADMIN_USER' \
DJANGO_SUPERUSER_EMAIL='admin@local' \
DJANGO_SUPERUSER_PASSWORD='$ADMIN_PASSWORD' \
'$VENV/bin/python' manage.py createsuperuser --noinput 2>/dev/null || true
"

if [[ "$SKIP_TEST_DEVICE" == false ]]; then
    log "Создание тестового устройства..."
    sudo -u "$SERVICE_USER" bash -c "cd '$PROJECT_DIR' && '$VENV/bin/python' manage.py create_test_device --name 'Тестовое устройство'" || true
fi

if [[ "$SKIP_BOT_TOKENS" == false ]]; then
    log "Генерация токенов для Telegram-бота..."
    sudo -u "$SERVICE_USER" bash -c "cd '$PROJECT_DIR' && '$VENV/bin/python' manage.py generate_tokens --count 10" || true
fi

log "Systemd: gunicorn..."
cat > /etc/systemd/system/fc_phones_django.service <<EOF
[Unit]
Description=FC Phones Django (Gunicorn)
After=network.target

[Service]
Type=exec
User=${SERVICE_USER}
Group=${SERVICE_USER}
WorkingDirectory=${PROJECT_DIR}
Environment=PATH=${VENV}/bin
ExecStart=${VENV}/bin/gunicorn fc_phones.wsgi:application \
    --bind 127.0.0.1:8000 \
    --workers ${GUNICORN_WORKERS} \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

log "Systemd: telegram bot..."
cat > /etc/systemd/system/fc_phones_bot.service <<EOF
[Unit]
Description=FC Phones Telegram Bot
After=network.target fc_phones_django.service

[Service]
Type=exec
User=${SERVICE_USER}
Group=${SERVICE_USER}
WorkingDirectory=${PROJECT_DIR}
Environment=PATH=${VENV}/bin
ExecStart=${VENV}/bin/python ${PROJECT_DIR}/bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

log "Nginx (HTTP, только IP)..."
cat > /etc/nginx/sites-available/${PROJECT_NAME} <<EOF
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name ${SERVER_IP} _;

    client_max_body_size 50M;

    access_log /var/log/nginx/fc_phones_access.log;
    error_log  /var/log/nginx/fc_phones_error.log;

    location /static/ {
        alias ${PROJECT_DIR}/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias ${PROJECT_DIR}/media/;
        expires 7d;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }
}
EOF

ln -sf /etc/nginx/sites-available/${PROJECT_NAME} /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

nginx -t

if [[ "$SKIP_FIREWALL" == false ]]; then
    log "Firewall..."
    mapfile -t SSH_PORTS < <(ss -tlnp 2>/dev/null | grep sshd | grep -oE ':[0-9]+' | tr -d ':' | sort -u)
    if [[ ${#SSH_PORTS[@]} -eq 0 ]]; then
        port=$(grep -E '^[[:space:]]*Port[[:space:]]+' /etc/ssh/sshd_config 2>/dev/null | awk '{print $2}' | tail -1)
        [[ -n "$port" ]] && SSH_PORTS=("$port") || SSH_PORTS=("22")
    fi
    for port in "${SSH_PORTS[@]}"; do
        ufw allow "${port}/tcp"
        ok "UFW: разрешён SSH порт ${port}"
    done
    ufw allow 80/tcp
    ufw --force enable
else
    warn "UFW пропущен (--skip-firewall)"
fi

log "Запуск сервисов..."
systemctl daemon-reload
systemctl enable fc_phones_django fc_phones_bot nginx
systemctl restart fc_phones_django fc_phones_bot nginx

sleep 2

log "Проверка..."
systemctl is-active --quiet fc_phones_django && ok "Django (gunicorn) работает" || fail "Django не запустился"
systemctl is-active --quiet fc_phones_bot      && ok "Telegram bot работает"   || warn "Bot не запустился — проверьте journalctl -u fc_phones_bot"
systemctl is-active --quiet nginx              && ok "Nginx работает"          || fail "Nginx не запустился"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://${SERVER_IP}/admin/login/" || echo "000")
[[ "$HTTP_CODE" == "200" ]] && ok "Админка отвечает HTTP $HTTP_CODE" || warn "Админка вернула HTTP $HTTP_CODE"

echo ""
echo "============================================"
ok "Деплой завершён"
echo "============================================"
echo ""
echo "  Админка:     http://${SERVER_IP}/admin/"
echo "  API docs:    http://${SERVER_IP}/api/docs/"
echo "  API base:    http://${SERVER_IP}/api/"
echo ""
echo "  Admin login: ${ADMIN_USER}"
echo ""
echo "  Мобильное приложение — BASE_URL:"
echo "    http://${SERVER_IP}/api/"
echo ""
echo "  Токены устройств — создайте в админке заново"
echo "  (старая БД на утерянном сервере недоступна)"
echo ""
echo "  Полезные команды:"
echo "    journalctl -u fc_phones_django -f"
echo "    journalctl -u fc_phones_bot -f"
echo "    systemctl restart fc_phones_django fc_phones_bot nginx"
echo ""
