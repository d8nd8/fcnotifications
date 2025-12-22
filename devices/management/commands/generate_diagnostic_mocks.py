"""
Management команда для генерации моков диагностических событий
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from devices.models import Device, DiagnosticEvent
import random
import uuid
from datetime import timedelta


class Command(BaseCommand):
    help = 'Генерирует моки диагностических событий для тестирования'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=100,
            help='Количество событий для генерации (по умолчанию: 100)',
        )
        parser.add_argument(
            '--device',
            type=str,
            help='Token устройства для которого генерировать события (если не указан - для всех устройств)',
        )

    def handle(self, *args, **options):
        count = options['count']
        device_token = options.get('device')
        
        # Получаем устройства
        if device_token:
            try:
                devices = [Device.objects.get(token=device_token)]
            except Device.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Устройство с токеном {device_token} не найдено'))
                return
        else:
            devices = list(Device.objects.all())
            if not devices:
                self.stdout.write(self.style.ERROR('Нет устройств в базе данных. Создайте хотя бы одно устройство.'))
                return
        
        self.stdout.write(f'Генерация {count} диагностических событий для {len(devices)} устройств...')
        
        # Данные для генерации
        severities = ['INFO', 'WARNING', 'ERROR', 'CRITICAL']
        components = ['APP', 'NOTIF_SERVICE', 'WORKER', 'NETWORK', 'SYSTEM']
        pipeline_stages = ['RECEIVE', 'STORE', 'QUEUE', 'SEND', 'UPLOAD', None]
        
        event_codes = {
            'APP': ['APP_START', 'APP_STOP', 'APP_CRASH', 'APP_MEMORY_LOW', 'APP_PERMISSION_DENIED'],
            'NOTIF_SERVICE': ['NOTIF_RECEIVED', 'NOTIF_FILTERED', 'NOTIF_SENT', 'NOTIF_FAILED', 'SERVICE_BOUND', 'SERVICE_UNBOUND'],
            'WORKER': ['WORKER_START', 'WORKER_STOP', 'WORKER_TASK_QUEUED', 'WORKER_TASK_FAILED', 'WORKER_RETRY'],
            'NETWORK': ['NETWORK_AVAILABLE', 'NETWORK_UNAVAILABLE', 'NETWORK_SWITCH', 'NETWORK_ERROR', 'UPLOAD_SUCCESS', 'UPLOAD_FAILED'],
            'SYSTEM': ['SYSTEM_DOZE', 'SYSTEM_BATTERY_LOW', 'SYSTEM_STORAGE_LOW', 'SYSTEM_RAM_LOW', 'SYSTEM_CPU_HIGH'],
        }
        
        created_count = 0
        now = timezone.now()
        
        for i in range(count):
            device = random.choice(devices)
            component = random.choice(components)
            severity = random.choice(severities)
            pipeline_stage = random.choice(pipeline_stages)
            
            # Генерируем timestamp (от 7 дней назад до сейчас)
            days_ago = random.randint(0, 7)
            hours_ago = random.randint(0, 23)
            minutes_ago = random.randint(0, 59)
            timestamp_dt = now - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
            timestamp = int(timestamp_dt.timestamp() * 1000)
            
            # Генерируем event_code на основе component
            event_code = random.choice(event_codes[component])
            
            # Генерируем state_snapshot
            state_snapshot = {
                'batteryLevel': random.randint(10, 100),
                'isCharging': random.choice([True, False]),
                'isNetworkAvailable': random.choice([True, False]),
                'isWifi': random.choice([True, False]) if random.choice([True, False]) else None,
                'isMobileData': random.choice([True, False]) if random.choice([True, False]) else None,
                'androidVersion': f'Android {random.randint(10, 14)}',
                'appVersion': f'{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 9)}',
                'deviceModel': random.choice(['Samsung Galaxy S23', 'Google Pixel 7', 'Xiaomi Mi 13', 'OnePlus 11', 'Sony Xperia 1 V']),
                'manufacturer': random.choice(['Samsung', 'Google', 'Xiaomi', 'OnePlus', 'Sony']),
                'screenOn': random.choice([True, False]),
                'isDoze': random.choice([True, False]),
                'isBatteryOptimized': random.choice([True, False]),
                'hasNotifPermission': random.choice([True, False]),
                'serviceBound': random.choice([True, False]),
                'queueSize': random.randint(0, 50),
                'lastCallbackTimestamp': timestamp - random.randint(0, 3600000),
                'serviceRunning': random.choice([True, False]),
                'workerRunning': random.choice([True, False]),
                'lastUploadTimestamp': timestamp - random.randint(0, 7200000),
                'networkType': random.choice(['WIFI', 'MOBILE', 'NONE', None]),
                'isBackgroundRestricted': random.choice([True, False]),
                'storageAvailable': random.choice([True, False]),
                'ramLow': random.choice([True, False]),
                'appStartTimestamp': timestamp - random.randint(3600000, 86400000),
                'uptimeMs': random.randint(3600000, 86400000),
                'workerPendingTasks': random.randint(0, 10),
                'uploadQueueSize': random.randint(0, 20),
                'cpuLoadPercent': random.randint(0, 100),
                'avgQueueInsertLatencyMs': random.randint(0, 1000),
                'avgProcessingLatencyMs': random.randint(0, 5000),
            }
            
            # Генерируем metrics_snapshot
            metrics_snapshot = {
                'totalCallbacksReceived': random.randint(100, 10000),
                'totalEventsSent': random.randint(50, 5000),
                'totalRetries': random.randint(0, 100),
                'totalServiceRestarts': random.randint(0, 20),
                'avgCallbackIntervalMs': random.randint(1000, 60000),
                'callbackGapMs': random.randint(0, 300000),
                'avgUploadLatencyMs': random.randint(100, 5000),
                'failuresSinceLastRecovery': random.randint(0, 10),
            }
            
            # Генерируем context
            context = {
                'errorMessage': f'Error message {i}' if severity in ['ERROR', 'CRITICAL'] else None,
                'retryCount': random.randint(0, 5) if severity in ['ERROR', 'CRITICAL'] else None,
                'networkType': state_snapshot.get('networkType'),
            }
            # Убираем None значения
            context = {k: v for k, v in context.items() if v is not None}
            
            # Создаем событие
            try:
                DiagnosticEvent.objects.create(
                    event_id=f'evt_{uuid.uuid4().hex[:12]}_{timestamp}',
                    device=device,
                    timestamp=timestamp,
                    event_code=event_code,
                    event_severity=severity,
                    component=component,
                    pipeline_stage=pipeline_stage,
                    context=context,
                    thread=f'Thread-{random.randint(1, 5)}',
                    attempt=random.randint(1, 3) if severity in ['ERROR', 'CRITICAL'] else None,
                    flow_id=f'flow_{uuid.uuid4().hex[:8]}' if random.choice([True, False]) else None,
                    state_snapshot=state_snapshot,
                    metrics_snapshot=metrics_snapshot,
                )
                created_count += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Ошибка при создании события {i}: {e}'))
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Успешно создано {created_count} диагностических событий из {count} запрошенных'
            )
        )
        
        # Показываем статистику
        self.stdout.write('\n📊 Статистика по созданным событиям:')
        for device in devices:
            count = DiagnosticEvent.objects.filter(device=device).count()
            self.stdout.write(f'  {device.name}: {count} событий')
