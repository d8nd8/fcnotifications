from django.core.management.base import BaseCommand
from devices.notification_filter import NotificationFilterService


class Command(BaseCommand):
    help = 'Создает фильтры уведомлений по умолчанию'

    def handle(self, *args, **options):
        self.stdout.write('Создание фильтров уведомлений по умолчанию...')
        
        try:
            NotificationFilterService.create_default_filters()
            self.stdout.write(
                self.style.SUCCESS('✅ Фильтры уведомлений успешно созданы!')
            )
            
            # Показываем созданные фильтры
            from devices.models import NotificationFilter
            filters = NotificationFilter.objects.all()
            
            self.stdout.write('\n📋 Созданные фильтры:')
            for filter_obj in filters:
                status = "✅" if filter_obj.is_active else "❌"
                filter_type = "🚫 Черный список" if filter_obj.filter_type == 'blacklist' else "✅ Белый список"
                self.stdout.write(f'  {status} {filter_obj.package_name} - {filter_type}')
                if filter_obj.description:
                    self.stdout.write(f'    Описание: {filter_obj.description}')
            
            self.stdout.write(f'\nВсего фильтров: {filters.count()}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка при создании фильтров: {e}')
            )
