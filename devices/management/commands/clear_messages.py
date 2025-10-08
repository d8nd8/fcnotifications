from django.core.management.base import BaseCommand
from devices.models import Message


class Command(BaseCommand):
    help = 'Очистка таблицы сообщений'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Подтвердить удаление всех сообщений',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    'ВНИМАНИЕ: Эта команда удалит ВСЕ сообщения из базы данных!\n'
                    'Для подтверждения используйте флаг --confirm'
                )
            )
            return

        # Подсчитываем количество сообщений
        total_messages = Message.objects.count()
        
        if total_messages == 0:
            self.stdout.write('Таблица сообщений уже пуста.')
            return

        self.stdout.write(f'Найдено {total_messages} сообщений для удаления...')
        
        # Удаляем все сообщения
        Message.objects.all().delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'Удалено {total_messages} сообщений')
        )
