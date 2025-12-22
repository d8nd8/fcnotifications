# Generated manually for DiagnosticEvent model

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0013_devicestatus'),
    ]

    operations = [
        migrations.CreateModel(
            name='DiagnosticEvent',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('event_id', models.CharField(db_index=True, max_length=255, unique=True, verbose_name='ID события')),
                ('timestamp', models.BigIntegerField(db_index=True, verbose_name='Время события (UNIX ms)')),
                ('event_code', models.CharField(db_index=True, max_length=100, verbose_name='Код события')),
                ('event_severity', models.CharField(choices=[('INFO', 'INFO'), ('WARNING', 'WARNING'), ('ERROR', 'ERROR'), ('CRITICAL', 'CRITICAL')], db_index=True, max_length=20, verbose_name='Уровень серьезности')),
                ('component', models.CharField(choices=[('APP', 'APP'), ('NOTIF_SERVICE', 'NOTIF_SERVICE'), ('WORKER', 'WORKER'), ('NETWORK', 'NETWORK'), ('SYSTEM', 'SYSTEM')], db_index=True, max_length=50, verbose_name='Компонент')),
                ('pipeline_stage', models.CharField(blank=True, choices=[('RECEIVE', 'RECEIVE'), ('STORE', 'STORE'), ('QUEUE', 'QUEUE'), ('SEND', 'SEND'), ('UPLOAD', 'UPLOAD')], db_index=True, max_length=50, null=True, verbose_name='Этап пайплайна')),
                ('context', models.JSONField(blank=True, default=dict, help_text='Произвольные дополнительные данные', verbose_name='Контекст события')),
                ('thread', models.CharField(blank=True, max_length=255, null=True, verbose_name='Поток выполнения')),
                ('attempt', models.IntegerField(blank=True, null=True, verbose_name='Номер попытки')),
                ('flow_id', models.CharField(blank=True, db_index=True, max_length=255, null=True, verbose_name='ID потока обработки')),
                ('state_snapshot', models.JSONField(blank=True, help_text='DeviceStateSnapshot - полное состояние устройства на момент события', null=True, verbose_name='Снимок состояния устройства')),
                ('metrics_snapshot', models.JSONField(blank=True, help_text='MetricsSnapshot - метрики производительности на момент события', null=True, verbose_name='Снимок метрик')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Создано')),
                ('device', models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name='diagnostic_events', to='devices.device', verbose_name='Устройство')),
            ],
            options={
                'verbose_name': 'Диагностическое событие',
                'verbose_name_plural': 'Диагностические события',
                'ordering': ['-timestamp', '-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='diagnosticevent',
            index=models.Index(fields=['device', '-timestamp'], name='devices_dia_device__idx'),
        ),
        migrations.AddIndex(
            model_name='diagnosticevent',
            index=models.Index(fields=['event_severity', '-timestamp'], name='devices_dia_event_s_idx'),
        ),
        migrations.AddIndex(
            model_name='diagnosticevent',
            index=models.Index(fields=['component', '-timestamp'], name='devices_dia_componen_idx'),
        ),
        migrations.AddIndex(
            model_name='diagnosticevent',
            index=models.Index(fields=['device', 'event_severity', '-timestamp'], name='devices_dia_device__idx2'),
        ),
    ]
