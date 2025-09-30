#!/usr/bin/env python3
"""
Simple synchronous Telegram bot for FC Phones project.
Uses requests instead of python-telegram-bot to avoid compatibility issues.
"""

import os
import sys
import django
import time
import json
import requests
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(project_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fc_phones.settings')
django.setup()

import logging
from django.conf import settings
from devices.models import Device, Message, BatteryReport, TelegramUser
from devices.notifications import notify

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class SimpleTelegramBot:
    def __init__(self, token):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.last_update_id = 0
        
    def get_updates(self):
        """Get updates from Telegram."""
        try:
            url = f"{self.base_url}/getUpdates"
            params = {
                'offset': self.last_update_id + 1,
                'timeout': 10
            }
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting updates: {e}")
            return None
    
    def send_message(self, chat_id, text, parse_mode='Markdown'):
        """Send message to chat."""
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': parse_mode
            }
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def handle_start(self, update):
        """Handle /start command."""
        user = update['message']['from']
        chat_id = update['message']['chat']['id']
        
        try:
            telegram_user, created = TelegramUser.objects.get_or_create(
                user_id=user['id'],
                defaults={
                    'username': user.get('username'),
                    'first_name': user.get('first_name'),
                    'last_name': user.get('last_name'),
                }
            )
            
            if not created:
                telegram_user.username = user.get('username')
                telegram_user.first_name = user.get('first_name')
                telegram_user.last_name = user.get('last_name')
                telegram_user.is_active = True
                telegram_user.save()
            
            status_text = "✅ Вы подписаны на уведомления!" if created else "✅ Подписка обновлена!"
            
            message = (
                f'🤖 **Сервис Алертов FC Phones**\n\n'
                f'{status_text}\n\n'
                'Доступные команды:\n'
                '/start - Показать это сообщение\n'
                '/devices - Список всех устройств\n'
                '/test - Отправить тестовое уведомление\n'
                '/help - Показать справку\n\n'
                '🔔 Здесь вы будете получать уведомления о новых сообщениях от устройств!'
            )
            
            self.send_message(chat_id, message)
            logger.info(f"User {user['id']} ({user.get('username')}) {'created' if created else 'updated'}")
            
        except Exception as e:
            logger.error(f"Error processing /start: {e}")
            self.send_message(chat_id, "❌ Произошла ошибка. Попробуйте позже.")
    
    def handle_help(self, update):
        """Handle /help command."""
        chat_id = update['message']['chat']['id']
        message = (
            '**Доступные команды:**\n\n'
            '/start - Показать приветственное сообщение\n'
            '/devices - Список всех устройств\n'
            '/test - Отправить тестовое уведомление\n'
            '/help - Показать эту справку\n\n'
            '**О сервисе:**\n'
            'Этот бот уведомляет о новых сообщениях от ваших устройств. '
            'Каждое сообщение будет приходить с информацией об устройстве, времени и отправителе.'
        )
        self.send_message(chat_id, message)
    
    def handle_devices(self, update):
        """Handle /devices command."""
        chat_id = update['message']['chat']['id']
        
        try:
            devices = Device.objects.all()[:10]  # Limit to 10 devices
            
            if not devices:
                self.send_message(chat_id, '❌ Устройства не найдены.')
                return
            
            message = '📱 **Список устройств:**\n\n'
            for device in devices:
                last_seen = device.last_seen.strftime('%d.%m.%Y %H:%M:%S') if device.last_seen else 'Никогда'
                status = '🟢 Онлайн' if device.last_seen else '🔴 Офлайн'
                message += f'• **{device.name}** {status}\n'
                message += f'  Токен: `{device.token}`\n'
                message += f'  Последняя активность: {last_seen}\n\n'
            
            self.send_message(chat_id, message)
            
        except Exception as e:
            logger.error(f"Error processing /devices: {e}")
            self.send_message(chat_id, "❌ Произошла ошибка при получении списка устройств.")
    
    def handle_test(self, update):
        """Handle /test command."""
        chat_id = update['message']['chat']['id']
        
        test_message = "🧪 <b>ТЕСТОВОЕ УВЕДОМЛЕНИЕ</b>\n\n"
        test_message += "📱 <b>Устройство:</b> Тестовое устройство\n"
        test_message += "⏰ <b>Время:</b> Сейчас\n"
        test_message += "👤 <b>Отправитель:</b> Система\n\n"
        test_message += "💬 <b>Сообщение:</b>\nЭто тестовое уведомление для проверки работы сервиса алертов."
        
        if notify(test_message):
            self.send_message(chat_id, '✅ Тестовое уведомление успешно отправлено!')
        else:
            self.send_message(chat_id, '❌ Не удалось отправить тестовое уведомление. Проверьте настройки бота.')
    
    def handle_message(self, update):
        """Handle incoming message."""
        message = update['message']
        text = message.get('text', '')
        
        if text.startswith('/start'):
            self.handle_start(update)
        elif text.startswith('/help'):
            self.handle_help(update)
        elif text.startswith('/devices'):
            self.handle_devices(update)
        elif text.startswith('/test'):
            self.handle_test(update)
        else:
            # Unknown command
            chat_id = message['chat']['id']
            self.send_message(chat_id, '❓ Неизвестная команда. Используйте /help для справки.')
    
    def run(self):
        """Main bot loop."""
        logger.info("Запуск простого синхронного бота...")
        logger.info("✅ Бот успешно запущен и готов к работе!")
        
        while True:
            try:
                updates = self.get_updates()
                if not updates or not updates.get('ok'):
                    time.sleep(1)
                    continue
                
                for update in updates.get('result', []):
                    self.last_update_id = update['update_id']
                    
                    if 'message' in update:
                        self.handle_message(update)
                
                time.sleep(0.1)  # Small delay to prevent overwhelming the API
                
            except KeyboardInterrupt:
                logger.info("Бот остановлен пользователем")
                break
            except Exception as e:
                logger.error(f"Ошибка в основном цикле: {e}")
                time.sleep(5)  # Wait before retrying


def main():
    """Start the bot."""
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set in environment variables")
        return
    
    bot = SimpleTelegramBot(settings.TELEGRAM_BOT_TOKEN)
    bot.run()


if __name__ == '__main__':
    main()
