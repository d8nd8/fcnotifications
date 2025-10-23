from django.core.management.base import BaseCommand
from django.utils import timezone
from devices.models import Device
from datetime import timedelta


class Command(BaseCommand):
    help = 'Обновляет статус устройств на основе последней активности'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Количество часов для определения онлайн статуса (по умолчанию: 24)'
        )
        parser.add_argument(
            '--show-details',
            action='store_true',
            help='Показать детальную информацию о каждом устройстве'
        )

    def handle(self, *args, **options):
        hours_threshold = options['hours']
        show_details = options['show_details']
        
        now = timezone.now()
        threshold_time = now - timedelta(hours=hours_threshold)
        
        # Получаем статистику
        total_devices = Device.objects.count()
        online_devices = Device.objects.filter(last_seen__gte=threshold_time).count()
        offline_devices = total_devices - online_devices
        
        self.stdout.write(f'Статистика устройств (порог: {hours_threshold} часов):')
        self.stdout.write(f'Всего устройств: {total_devices}')
        self.stdout.write(f'Онлайн: {online_devices}')
        self.stdout.write(f'Офлайн: {offline_devices}')
        self.stdout.write('')
        
        if show_details:
            self.stdout.write('Детальная информация:')
            self.stdout.write('-' * 80)
            
            for device in Device.objects.all().order_by('-last_seen'):
                if device.last_seen:
                    if device.last_seen >= threshold_time:
                        status = '🟢 ОНЛАЙН'
                        time_info = f'{device.last_seen.strftime("%d.%m.%Y %H:%M:%S")}'
                    else:
                        hours_ago = int((now - device.last_seen).total_seconds() / 3600)
                        status = f'🟡 {hours_ago}ч назад'
                        time_info = f'{device.last_seen.strftime("%d.%m.%Y %H:%M:%S")}'
                else:
                    status = '🔴 ОФЛАЙН'
                    time_info = 'Никогда'
                
                self.stdout.write(
                    f'{status} | {device.name:<20} | {time_info} | {device.token}'
                )
        
        # Показываем устройства, которые давно не были активны
        old_devices = Device.objects.filter(
            last_seen__lt=threshold_time
        ).exclude(last_seen__isnull=True).order_by('last_seen')
        
        if old_devices.exists():
            self.stdout.write('')
            self.stdout.write('Устройства, которые давно не были активны:')
            for device in old_devices[:10]:  # Показываем только первые 10
                hours_ago = int((now - device.last_seen).total_seconds() / 3600)
                self.stdout.write(
                    f'  {device.name} - {hours_ago}ч назад ({device.last_seen.strftime("%d.%m.%Y %H:%M")})'
                )
