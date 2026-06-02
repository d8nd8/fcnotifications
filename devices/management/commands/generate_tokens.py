from django.core.management.base import BaseCommand
from devices.models import AuthToken
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

        for _ in range(count):
            while True:
                token = ''.join(
                    secrets.choice(string.ascii_uppercase + string.digits)
                    for _ in range(length)
                )
                if not AuthToken.objects.filter(token=token).exists():
                    break

            AuthToken.objects.create(token=token)
            created_count += 1
            self.stdout.write(f'  Создан токен: {token}')

        self.stdout.write(
            self.style.SUCCESS(f'\nСоздано {created_count} токенов')
        )

        unused = AuthToken.objects.filter(is_used=False).count()
        used = AuthToken.objects.filter(is_used=True).count()

        self.stdout.write(f'Всего неиспользованных токенов: {unused}')
        self.stdout.write(f'Использованных токенов: {used}')
