from django.db import models
import uuid
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Device(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.UUIDField(_('Токен'), unique=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('Название'), max_length=255)
    last_seen = models.DateTimeField(_('Последний раз онлайн'), null=True, blank=True)
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.token})"

    @property
    def is_authenticated(self):
        """Для совместимости с DRF permissions"""
        return True

    @property
    def is_anonymous(self):
        """Для совместимости с DRF permissions"""
        return False

    class Meta:
        verbose_name = _('Устройство')
        verbose_name_plural = _('Устройства')
        ordering = ['-created_at']


class BatteryReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='battery_reports', verbose_name=_('Устройство'))
    battery_level = models.IntegerField(_('Уровень батареи'))  # 0-100
    date_created = models.DateTimeField(_('Дата создания'), default=timezone.now)
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True)

    def __str__(self):
        return f"Battery {self.battery_level}% - {self.device.name}"

    class Meta:
        verbose_name = _('Отчет о батарее')
        verbose_name_plural = _('Отчеты о батарее')
        ordering = ['-date_created']

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.battery_level < 0 or self.battery_level > 100:
            raise ValidationError('Battery level must be between 0 and 100')


class TelegramUser(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.BigIntegerField(_('Telegram User ID'), unique=True)
    username = models.CharField(_('Username'), max_length=255, null=True, blank=True)
    first_name = models.CharField(_('Имя'), max_length=255, null=True, blank=True)
    last_name = models.CharField(_('Фамилия'), max_length=255, null=True, blank=True)
    is_active = models.BooleanField(_('Активен'), default=True)
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True)
    last_activity = models.DateTimeField(_('Последняя активность'), auto_now=True)

    def __str__(self):
        name = f"{self.first_name} {self.last_name}".strip() or self.username or f"User {self.user_id}"
        return f"{name} (@{self.username})" if self.username else name

    class Meta:
        verbose_name = _('Пользователь Telegram')
        verbose_name_plural = _('Пользователи Telegram')
        ordering = ['-created_at']


class AuthToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.CharField(_('Токен'), max_length=32, unique=True)
    is_used = models.BooleanField(_('Использован'), default=False)
    used_by = models.ForeignKey(TelegramUser, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('Использован пользователем'))
    created_at = models.DateTimeField(_('Создан'), auto_now_add=True)
    used_at = models.DateTimeField(_('Использован'), null=True, blank=True)

    def __str__(self):
        status = "✅ Использован" if self.is_used else "⏳ Не использован"
        return f"{self.token} - {status}"

    class Meta:
        verbose_name = _('Токен авторизации')
        verbose_name_plural = _('Токены авторизации')
        ordering = ['-created_at']


class NotificationFilter(models.Model):
    """
    Модель для хранения правил фильтрации уведомлений
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    package_name = models.CharField(_('Имя пакета'), max_length=255, unique=True, help_text=_('Имя пакета приложения (например: com.android.systemui)'))
    description = models.CharField(_('Описание'), max_length=500, blank=True, help_text=_('Описание для чего используется этот пакет'))
    is_active = models.BooleanField(_('Активен'), default=True, help_text=_('Включена ли фильтрация для этого пакета'))
    filter_type = models.CharField(
        _('Тип фильтра'),
        max_length=20,
        choices=[
            ('blacklist', _('Черный список - блокировать')),
            ('whitelist', _('Белый список - разрешить')),
        ],
        default='blacklist',
        help_text=_('Тип фильтрации')
    )
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Обновлено'), auto_now=True)

    def __str__(self):
        status = "✅" if self.is_active else "❌"
        return f"{status} {self.package_name} ({self.get_filter_type_display()})"

    class Meta:
        verbose_name = _('Фильтр уведомлений')
        verbose_name_plural = _('Фильтры уведомлений')
        ordering = ['package_name']


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='messages', verbose_name=_('Устройство'))
    date_created = models.DateTimeField(_('Дата создания'), default=timezone.now)
    sender = models.CharField(_('Отправитель'), max_length=255)
    text = models.TextField(_('Текст сообщения'))
    package_name = models.CharField(_('Имя пакета'), max_length=255, blank=True, help_text=_('Имя пакета приложения, отправившего уведомление'))
    is_filtered = models.BooleanField(_('Отфильтровано'), default=False, help_text=_('Было ли уведомление отфильтровано'))
    filter_reason = models.CharField(_('Причина фильтрации'), max_length=500, blank=True, help_text=_('Причина, по которой уведомление было отфильтровано'))
    raw_payload = models.JSONField(_('Исходные данные'), default=dict, blank=True)
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True)

    def __str__(self):
        filtered = " [FILTERED]" if self.is_filtered else ""
        return f"Message from {self.sender} - {self.device.name}{filtered}"

    class Meta:
        verbose_name = _('Сообщение')
        verbose_name_plural = _('Сообщения')
        ordering = ['-date_created']


class LogFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='log_files', verbose_name=_('Устройство'))
    file = models.FileField(_('Файл лога'), upload_to='logs/', null=True, blank=True)
    text = models.TextField(_('Текст лога'), blank=True, help_text=_('Превью текста для отображения в админке'))
    date_created = models.DateTimeField(_('Дата создания'), default=timezone.now)
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True)

    def __str__(self):
        return f"Log from {self.device.name} - {self.date_created.strftime('%d.%m.%Y %H:%M')}"

    class Meta:
        verbose_name = _('Лог файл')
        verbose_name_plural = _('Лог файлы')
        ordering = ['-date_created']


class DeviceStatus(models.Model):
    """
    Модель для хранения расширенной информации о статусе устройства
    """
    STATUS_CHOICES = [
        ('SUCCESS', 'SUCCESS - Всё хорошо'),
        ('ATTENTION', 'ATTENTION - Требуется внимание'),
        ('ERROR', 'ERROR - Критическая ошибка'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='status_reports', verbose_name=_('Устройство'))
    
    # Основные поля статуса
    status_level = models.CharField(
        _('Статус устройства'), 
        max_length=20, 
        choices=STATUS_CHOICES,
        help_text=_('Общий статус устройства')
    )
    reasons = models.JSONField(
        _('Причины статуса'), 
        default=list, 
        blank=True,
        help_text=_('Список текстовых причин текущего состояния')
    )
    
    # Информация о батарее
    battery_level = models.IntegerField(
        _('Уровень батареи'), 
        help_text=_('Уровень заряда батареи в процентах (0-100)')
    )
    is_charging = models.BooleanField(
        _('Заряжается'), 
        default=False,
        help_text=_('Заряжается ли устройство сейчас')
    )
    
    # Сетевая информация
    network_available = models.BooleanField(
        _('Доступ к интернету'), 
        default=True,
        help_text=_('Есть ли доступ к интернету')
    )
    
    # Информация об уведомлениях
    unsent_notifications = models.IntegerField(
        _('Неотправленные уведомления'), 
        default=0,
        help_text=_('Количество неотправленных уведомлений')
    )
    last_notification_timestamp = models.DateTimeField(
        _('Последнее уведомление'), 
        null=True, 
        blank=True,
        help_text=_('Время последнего полученного уведомления')
    )
    
    # Техническая информация
    timestamp = models.BigIntegerField(
        _('Время отчёта (UNIX)'), 
        help_text=_('Время формирования отчёта в миллисекундах UNIX')
    )
    app_version = models.CharField(
        _('Версия приложения'), 
        max_length=50, 
        blank=True,
        help_text=_('Версия мобильного приложения')
    )
    android_version = models.CharField(
        _('Версия Android'), 
        max_length=50, 
        blank=True,
        help_text=_('Версия операционной системы Android')
    )
    device_model = models.CharField(
        _('Модель устройства'), 
        max_length=255, 
        blank=True,
        help_text=_('Модель устройства (например, Samsung Galaxy S23)')
    )
    
    # Метаданные
    date_created = models.DateTimeField(_('Дата создания'), default=timezone.now)
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True)

    def __str__(self):
        return f"Status {self.status_level} - {self.device.name} ({self.date_created.strftime('%d.%m.%Y %H:%M')})"

    class Meta:
        verbose_name = _('Статус устройства')
        verbose_name_plural = _('Статусы устройств')
        ordering = ['-date_created']

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.battery_level < 0 or self.battery_level > 100:
            raise ValidationError('Battery level must be between 0 and 100')


class DiagnosticEvent(models.Model):
    """
    Модель для хранения диагностических событий от мобильных устройств
    """
    SEVERITY_CHOICES = [
        ('INFO', 'INFO'),
        ('WARNING', 'WARNING'),
        ('ERROR', 'ERROR'),
        ('CRITICAL', 'CRITICAL'),
    ]
    
    COMPONENT_CHOICES = [
        ('APP', 'APP'),
        ('NOTIF_SERVICE', 'NOTIF_SERVICE'),
        ('WORKER', 'WORKER'),
        ('NETWORK', 'NETWORK'),
        ('SYSTEM', 'SYSTEM'),
    ]
    
    PIPELINE_STAGE_CHOICES = [
        ('RECEIVE', 'RECEIVE'),
        ('STORE', 'STORE'),
        ('QUEUE', 'QUEUE'),
        ('SEND', 'SEND'),
        ('UPLOAD', 'UPLOAD'),
    ]
    
    # Основные поля
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_id = models.CharField(_('ID события'), max_length=255, unique=True, db_index=True)
    device = models.ForeignKey(
        Device, 
        on_delete=models.CASCADE, 
        related_name='diagnostic_events',
        verbose_name=_('Устройство'),
        db_index=True
    )
    timestamp = models.BigIntegerField(_('Время события (UNIX ms)'), db_index=True)
    
    # Классификация события
    event_code = models.CharField(_('Код события'), max_length=100, db_index=True)
    event_severity = models.CharField(
        _('Уровень серьезности'), 
        max_length=20, 
        choices=SEVERITY_CHOICES,
        db_index=True
    )
    component = models.CharField(
        _('Компонент'), 
        max_length=50, 
        choices=COMPONENT_CHOICES,
        db_index=True
    )
    pipeline_stage = models.CharField(
        _('Этап пайплайна'), 
        max_length=50, 
        choices=PIPELINE_STAGE_CHOICES,
        null=True, 
        blank=True,
        db_index=True
    )
    
    # Контекст и отладка
    context = models.JSONField(
        _('Контекст события'), 
        default=dict, 
        blank=True,
        help_text=_('Произвольные дополнительные данные')
    )
    thread = models.CharField(_('Поток выполнения'), max_length=255, null=True, blank=True)
    attempt = models.IntegerField(_('Номер попытки'), null=True, blank=True)
    flow_id = models.CharField(_('ID потока обработки'), max_length=255, null=True, blank=True, db_index=True)
    
    # Снимки состояния (полные JSON объекты)
    state_snapshot = models.JSONField(
        _('Снимок состояния устройства'), 
        null=True, 
        blank=True,
        help_text=_('DeviceStateSnapshot - полное состояние устройства на момент события')
    )
    metrics_snapshot = models.JSONField(
        _('Снимок метрик'), 
        null=True, 
        blank=True,
        help_text=_('MetricsSnapshot - метрики производительности на момент события')
    )
    
    # Метаданные
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True, db_index=True)
    
    class Meta:
        verbose_name = _('Диагностическое событие')
        verbose_name_plural = _('Диагностические события')
        ordering = ['-timestamp', '-created_at']
        indexes = [
            models.Index(fields=['device', '-timestamp']),
            models.Index(fields=['event_severity', '-timestamp']),
            models.Index(fields=['component', '-timestamp']),
            models.Index(fields=['device', 'event_severity', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.event_code} [{self.event_severity}] - {self.device.name} ({self.get_timestamp_display()})"
    
    def get_timestamp_display(self):
        """Возвращает читаемое представление timestamp"""
        from datetime import datetime
        try:
            dt = datetime.fromtimestamp(self.timestamp / 1000)
            return dt.strftime('%d.%m.%Y %H:%M:%S')
        except (ValueError, TypeError):
            return str(self.timestamp)

