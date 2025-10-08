from django.core.management.base import BaseCommand
from devices.models import NotificationFilter
from devices.notification_filter import NotificationFilterService


class Command(BaseCommand):
    help = 'Настройка фильтров уведомлений для блокировки спама'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Удалить все существующие фильтры перед созданием новых',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('Удаление существующих фильтров...')
            NotificationFilter.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS('Все фильтры удалены')
            )

        # Создаем фильтры на основе анализа базы данных
        filters_to_create = [
            # SMS сообщения - РАЗРЕШАЕМ только важные SMS
            {
                'package_name': 'com.google.android.apps.messaging',
                'description': 'SMS сообщения - разрешаем только важные SMS от банков и операторов',
                'filter_type': 'whitelist',
                'is_active': True
            },
            # Ваше приложение - блокируем служебные сообщения
            {
                'package_name': 'com.onlyone.app.FC',
                'description': 'FC приложение - блокируем служебные сообщения',
                'filter_type': 'blacklist',
                'is_active': True
            },
            # Системные уведомления Android
            {
                'package_name': 'com.android.systemui',
                'description': 'Системный интерфейс Android - блокируем системные уведомления',
                'filter_type': 'blacklist',
                'is_active': True
            },
            # Магазины приложений
            {
                'package_name': 'ru.vk.store',
                'description': 'VK Store - блокируем уведомления магазина',
                'filter_type': 'blacklist',
                'is_active': True
            },
            {
                'package_name': 'com.android.vending',
                'description': 'Google Play Store - блокируем уведомления магазина',
                'filter_type': 'blacklist',
                'is_active': True
            },
            {
                'package_name': 'com.transsnet.store',
                'description': 'Transsnet Store - блокируем уведомления магазина',
                'filter_type': 'blacklist',
                'is_active': True
            },
            # Xiaomi системные приложения
            {
                'package_name': 'com.xiaomi.mipicks',
                'description': 'Xiaomi Mi Picks - блокируем системные уведомления',
                'filter_type': 'blacklist',
                'is_active': True
            },
            {
                'package_name': 'com.xiaomi.discover',
                'description': 'Xiaomi Discover - блокируем системные уведомления',
                'filter_type': 'blacklist',
                'is_active': True
            },
            # Google системные приложения
            {
                'package_name': 'com.google.android.setupwizard',
                'description': 'Google Setup Wizard - блокируем системные уведомления',
                'filter_type': 'blacklist',
                'is_active': True
            },
            {
                'package_name': 'com.google.android.gms',
                'description': 'Google Mobile Services - блокируем системные уведомления',
                'filter_type': 'blacklist',
                'is_active': True
            },
            {
                'package_name': 'com.google.android.dialer',
                'description': 'Google Dialer - блокируем системные уведомления',
                'filter_type': 'blacklist',
                'is_active': True
            },
            # OPPO системные приложения
            {
                'package_name': 'com.oppo.ota',
                'description': 'OPPO OTA - блокируем уведомления об обновлениях',
                'filter_type': 'blacklist',
                'is_active': True
            },
            # Другие системные приложения
            {
                'package_name': 'com.sh.smart.caller',
                'description': 'Smart Caller - блокируем системные уведомления',
                'filter_type': 'blacklist',
                'is_active': True
            },
            {
                'package_name': 'com.nearme.romupdate',
                'description': 'Nearme ROM Update - блокируем уведомления об обновлениях',
                'filter_type': 'blacklist',
                'is_active': True
            },
            {
                'package_name': 'com.sprd.omacp',
                'description': 'Spreadtrum OMACP - блокируем системные уведомления',
                'filter_type': 'blacklist',
                'is_active': True
            },
            {
                'package_name': 'com.google.android.apps.wellbeing',
                'description': 'Google Wellbeing - блокируем системные уведомления',
                'filter_type': 'blacklist',
                'is_active': True
            },
            {
                'package_name': 'com.android.providers.downloads',
                'description': 'Android Downloads Provider - блокируем системные уведомления',
                'filter_type': 'blacklist',
                'is_active': True
            },
            {
                'package_name': 'com.miui.securitycenter',
                'description': 'MIUI Security Center - блокируем системные уведомления',
                'filter_type': 'blacklist',
                'is_active': True
            },
            {
                'package_name': 'com.miui.msa.global',
                'description': 'MIUI MSA Global - блокируем системные уведомления',
                'filter_type': 'blacklist',
                'is_active': True
            },
            # Паттерны для блокировки всех системных пакетов
            {
                'package_name': 'com.android.*',
                'description': 'Все системные пакеты Android',
                'filter_type': 'blacklist',
                'is_active': True
            },
            {
                'package_name': 'com.google.android.*',
                'description': 'Все системные пакеты Google',
                'filter_type': 'blacklist',
                'is_active': True
            },
            {
                'package_name': 'com.xiaomi.*',
                'description': 'Все системные пакеты Xiaomi',
                'filter_type': 'blacklist',
                'is_active': True
            },
            {
                'package_name': 'com.oppo.*',
                'description': 'Все системные пакеты OPPO',
                'filter_type': 'blacklist',
                'is_active': True
            },
            {
                'package_name': 'com.miui.*',
                'description': 'Все системные пакеты MIUI',
                'filter_type': 'blacklist',
                'is_active': True
            },
        ]

        created_count = 0
        updated_count = 0

        for filter_data in filters_to_create:
            filter_obj, created = NotificationFilter.objects.get_or_create(
                package_name=filter_data['package_name'],
                defaults={
                    'description': filter_data['description'],
                    'filter_type': filter_data['filter_type'],
                    'is_active': filter_data['is_active']
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Создан фильтр: {filter_obj.package_name}')
                )
            else:
                # Обновляем существующий фильтр
                filter_obj.description = filter_data['description']
                filter_obj.filter_type = filter_data['filter_type']
                filter_obj.is_active = filter_data['is_active']
                filter_obj.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Обновлен фильтр: {filter_obj.package_name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nФильтры настроены: создано {created_count}, обновлено {updated_count}'
            )
        )

        # Показываем статистику
        total_filters = NotificationFilter.objects.count()
        active_filters = NotificationFilter.objects.filter(is_active=True).count()
        
        self.stdout.write(f'Всего фильтров: {total_filters}')
        self.stdout.write(f'Активных фильтров: {active_filters}')
        
        # Показываем примеры фильтрации
        self.stdout.write('\nПримеры фильтрации:')
        test_packages = [
            'com.onlyone.app.FC',
            'com.android.systemui', 
            'com.google.android.apps.messaging',
            'ru.vk.store'
        ]
        
        for package in test_packages:
            should_filter, reason = NotificationFilterService.should_filter_notification(package)
            status = "🚫 БЛОКИРОВАНО" if should_filter else "✅ РАЗРЕШЕНО"
            self.stdout.write(f'  {package}: {status} ({reason})')
