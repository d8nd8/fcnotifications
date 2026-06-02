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

    def handle(self, *args, **options):
        name = options['name']
        token = options['token'] or str(uuid.uuid4())

        if Device.objects.filter(token=token).exists():
            self.stdout.write(
                self.style.WARNING(f'Устройство с токеном {token} уже существует')
            )
            return

        device = Device.objects.create(
            name=name,
            token=token,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Устройство успешно создано:\n'
                f'  ID: {device.id}\n'
                f'  Название: {device.name}\n'
                f'  Токен: {device.token}'
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                '\nПримеры API запросов:\n'
                f'# Получить информацию об устройстве:\n'
                f'curl -H "X-TOKEN: {device.token}" http://localhost:8000/api/device\n\n'
                f'# Отправить отчет о батарее:\n'
                f'curl -X POST -H "Content-Type: application/json" \\\n'
                f'  -d \'{{"token": "{device.token}", "battery_level": 85}}\' \\\n'
                f'  http://localhost:8000/api/battery-report\n\n'
                f'# Отправить сообщение:\n'
                f'curl -X POST -H "X-TOKEN: {device.token}" -H "Content-Type: application/json" \\\n'
                f'  -d \'{{"sender": "Тестовый пользователь", "text": "Привет от тестового устройства!"}}\' \\\n'
                f'  http://localhost:8000/api/mobile/message'
            )
        )
