from django.core.management.base import BaseCommand
from devices.models import TelegramUser
import secrets
import string


class Command(BaseCommand):
    help = 'Генерация токенов авторизации для Telegram бота'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Количество токенов для генерации (по умолчанию 10)',
        )
        parser.add_argument(
            '--length',
            type=int,
            default=16,
            help='Длина токена (по умолчанию 16)',
        )

    def handle(self, *args, **options):
        count = options['count']
        length = options['length']
        
        self.stdout.write(f'Генерация {count} токенов длиной {length} символов...')
        
        created_count = 0
        
        for i in range(count):
            # Генерируем уникальный токен
            while True:
                token = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(length))
                
                # Проверяем, что токен уникален
                if not TelegramUser.objects.filter(token=token).exists():
                    break
            
            # Создаем токен без привязки к пользователю
            # Используем отрицательный ID для токенов, чтобы избежать конфликтов
            TelegramUser.objects.create(
                user_id=-(i+1),  # Отрицательный ID для токенов
                username=None,  # Без username
                first_name=None,  # Без имени
                last_name=None,  # Без фамилии
                token=token,
                is_active=False  # Токен неактивен до использования
            )
            
            created_count += 1
            self.stdout.write(f'  Создан токен: {token}')
        
        self.stdout.write(
            self.style.SUCCESS(f'\nСоздано {created_count} токенов')
        )
        
        # Показываем статистику
        total_tokens = TelegramUser.objects.filter(is_active=False).count()
        used_tokens = TelegramUser.objects.filter(is_active=True).count()
        
        self.stdout.write(f'Всего неиспользованных токенов: {total_tokens}')
        self.stdout.write(f'Использованных токенов: {used_tokens}')
