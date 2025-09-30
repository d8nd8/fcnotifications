#!/bin/bash

# FC Phones - Setup Script

echo "🚀 Настройка FC Phones Django REST API..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не установлен. Пожалуйста, установите Python 3 сначала."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Активация виртуального окружения..."
source venv/bin/activate

# Install dependencies
echo "📥 Установка зависимостей..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️ Создание файла .env..."
    cp env.example .env
    echo "⚠️  Пожалуйста, отредактируйте файл .env с вашими настройками перед запуском сервера."
fi

# Run migrations
echo "🗄️ Выполнение миграций базы данных..."
python manage.py migrate

# Create superuser (optional)
echo "👤 Создание суперпользователя (опционально)..."
echo "Вы можете пропустить этот шаг, нажав Ctrl+C"
python manage.py createsuperuser

# Create test device
echo "📱 Создание тестового устройства..."
python manage.py create_test_device --name "Мой телефон"

echo "✅ Настройка завершена!"
echo ""
echo "Для запуска сервера:"
echo "  source venv/bin/activate"
echo "  python manage.py runserver"
echo ""
echo "Для запуска Telegram бота:"
echo "  source venv/bin/activate"
echo "  python bot.py"
echo ""
echo "Не забудьте настроить файл .env с настройками Telegram бота!"
