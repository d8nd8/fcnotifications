from django.core.management.base import BaseCommand
from devices.models import Message
from devices.notification_filter import NotificationFilterService


class Command(BaseCommand):
    help = 'Тестирование фильтров уведомлений на реальных данных'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Количество сообщений для тестирования (по умолчанию 50)',
        )
        parser.add_argument(
            '--package',
            type=str,
            help='Тестировать только сообщения от конкретного пакета',
        )

    def handle(self, *args, **options):
        limit = options['limit']
        package_filter = options['package']
        
        # Получаем сообщения для тестирования
        queryset = Message.objects.all()
        if package_filter:
            queryset = queryset.filter(sender=package_filter)
        
        messages = list(queryset.order_by('-created_at')[:limit])
        
        if not messages:
            self.stdout.write('Нет сообщений для тестирования')
            return
        
        self.stdout.write(f'Тестирование фильтров на {len(messages)} сообщениях...\n')
        
        filtered_count = 0
        allowed_count = 0
        
        for message in messages:
            # Используем sender как package_name, так как в базе package_name пустое
            package_name = message.package_name or message.sender
            should_filter, reason = NotificationFilterService.should_filter_notification(
                package_name=package_name,
                sender=message.sender,
                text=message.text
            )
            
            if should_filter:
                filtered_count += 1
                status = "🚫 БЛОКИРОВАНО"
                color = self.style.ERROR
            else:
                allowed_count += 1
                status = "✅ РАЗРЕШЕНО"
                color = self.style.SUCCESS
            
            self.stdout.write(
                color(f'{status} | {message.sender} | {message.text[:50]}...')
            )
            if should_filter:
                self.stdout.write(f'    Причина: {reason}')
            self.stdout.write('')
        
        # Статистика
        total = len(messages)
        self.stdout.write('=' * 60)
        self.stdout.write(f'Всего сообщений: {total}')
        self.stdout.write(f'Будет заблокировано: {filtered_count} ({filtered_count/total*100:.1f}%)')
        self.stdout.write(f'Будет разрешено: {allowed_count} ({allowed_count/total*100:.1f}%)')
        
        # Показываем топ пакетов
        self.stdout.write('\nТоп пакетов по количеству сообщений:')
        package_stats = {}
        for message in messages:
            package = message.sender
            if package not in package_stats:
                package_stats[package] = {'total': 0, 'filtered': 0}
            package_stats[package]['total'] += 1
            
            should_filter, _ = NotificationFilterService.should_filter_notification(
                package_name=message.sender,
                sender=message.sender,
                text=message.text
            )
            if should_filter:
                package_stats[package]['filtered'] += 1
        
        for package, stats in sorted(package_stats.items(), key=lambda x: x[1]['total'], reverse=True):
            if stats['total'] > 0:
                filtered_pct = stats['filtered'] / stats['total'] * 100
                self.stdout.write(
                    f'  {package}: {stats["total"]} сообщений, '
                    f'{stats["filtered"]} заблокировано ({filtered_pct:.1f}%)'
                )
