from django.core.management.base import BaseCommand
from devices.models import Device
import requests
import json
import random


class Command(BaseCommand):
    help = 'Тестирует отправку отчета о батарее'

    def add_arguments(self, parser):
        parser.add_argument(
            '--device-id',
            type=str,
            help='ID конкретного устройства (если не указан, выбирается первое)'
        )
        parser.add_argument(
            '--base-url',
            type=str,
            default='http://localhost:8000',
            help='Базовый URL API (по умолчанию: http://localhost:8000)'
        )
        parser.add_argument(
            '--count',
            type=int,
            default=3,
            help='Количество отчетов для отправки (по умолчанию: 3)'
        )

    def handle(self, *args, **options):
        device_id = options.get('device_id')
        base_url = options['base_url']
        count = options['count']
        
        # Выбираем устройство
        if device_id:
            try:
                device = Device.objects.get(id=device_id)
            except Device.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Устройство с ID {device_id} не найдено')
                )
                return
        else:
            device = Device.objects.first()
            if not device:
                self.stdout.write(
                    self.style.ERROR('Нет устройств в системе')
                )
                return
        
        self.stdout.write(f'Тестирование простой ручки для устройства: {device.name}')
        self.stdout.write(f'Токен: {device.token}')
        self.stdout.write(f'URL: {base_url}/api/battery-report')
        self.stdout.write('')
        
        success_count = 0
        error_count = 0
        
        for i in range(count):
            # Генерируем случайный уровень батареи
            battery_level = random.randint(10, 100)
            
            # Данные для отправки
            data = {
                'token': str(device.token),
                'battery_level': battery_level
            }
            
            try:
                # Отправляем POST запрос
                response = requests.post(
                    f'{base_url}/api/battery-report',
                    json=data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    success_count += 1
                    result = response.json()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'[{i+1}/{count}] ✅ Отчет отправлен: {battery_level}% - {result.get("message", "")}'
                        )
                    )
                else:
                    error_count += 1
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('error', response.text)
                    except:
                        error_msg = response.text
                    
                    self.stdout.write(
                        self.style.ERROR(
                            f'[{i+1}/{count}] ❌ Ошибка {response.status_code}: {error_msg}'
                        )
                    )
                
            except requests.exceptions.RequestException as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'[{i+1}/{count}] ❌ Ошибка сети: {str(e)}'
                    )
                )
        
        # Итоговая статистика
        self.stdout.write('')
        self.stdout.write('=' * 50)
        self.stdout.write(f'Итого отправлено: {success_count + error_count}')
        self.stdout.write(f'Успешно: {success_count}')
        self.stdout.write(f'Ошибок: {error_count}')
        
        if success_count > 0:
            # Проверяем обновление last_seen
            device.refresh_from_db()
            if device.last_seen:
                self.stdout.write(f'Последняя активность обновлена: {device.last_seen.strftime("%d.%m.%Y %H:%M:%S")}')
            else:
                self.stdout.write('⚠️  last_seen не обновился')
        
        # Показываем пример использования
        self.stdout.write('')
        self.stdout.write('Пример использования:')
        self.stdout.write(f'curl -X POST {base_url}/api/battery-report \\')
        self.stdout.write('  -H "Content-Type: application/json" \\')
        self.stdout.write(f'  -d \'{{"token": "{device.token}", "battery_level": 75}}\'')
