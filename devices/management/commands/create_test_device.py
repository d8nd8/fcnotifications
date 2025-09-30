from django.core.management.base import BaseCommand
from devices.models import Device
import uuid


class Command(BaseCommand):
    help = 'Создать тестовое устройство с известным токеном для тестирования'

    def add_arguments(self, parser):
        parser.add_argument(
            '--name',
            type=str,
            default='Тестовое устройство',
            help='Название устройства (по умолчанию: Тестовое устройство)'
        )
        parser.add_argument(
            '--token',
            type=str,
            help='Пользовательский токен (если не указан, будет сгенерирован случайный)'
        )
        parser.add_argument(
            '--external-id',
            type=str,
            help='Внешний ID для устройства'
        )

    def handle(self, *args, **options):
        name = options['name']
        token = options['token'] or str(uuid.uuid4())
        external_id = options['external_id']

        # Check if device with this token already exists
        if Device.objects.filter(token=token).exists():
            self.stdout.write(
                self.style.WARNING(f'Устройство с токеном {token} уже существует')
            )
            return

        # Create device
        device = Device.objects.create(
            name=name,
            token=token,
            external_id=external_id
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Устройство успешно создано:\n'
                f'  ID: {device.id}\n'
                f'  Название: {device.name}\n'
                f'  Токен: {device.token}\n'
                f'  Внешний ID: {device.external_id or "Не указан"}'
            )
        )

        # Show example curl commands
        self.stdout.write(
            self.style.SUCCESS(
                '\nПримеры API запросов:\n'
                f'# Получить информацию об устройстве:\n'
                f'curl -H "X-TOKEN: {device.token}" http://localhost:8000/api/device\n\n'
                f'# Отправить отчет о батарее:\n'
                f'curl -X POST -H "X-TOKEN: {device.token}" -H "Content-Type: application/json" \\\n'
                f'  -d \'{{"battery_level": 85, "date_created": "2024-01-01T12:00:00Z"}}\' \\\n'
                f'  http://localhost:8000/api/mobile/battery\n\n'
                f'# Отправить сообщение:\n'
                f'curl -X POST -H "X-TOKEN: {device.token}" -H "Content-Type: application/json" \\\n'
                f'  -d \'{{"sender": "Тестовый пользователь", "text": "Привет от тестового устройства!"}}\' \\\n'
                f'  http://localhost:8000/api/mobile/message'
            )
        )
