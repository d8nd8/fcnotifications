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
    token = models.CharField(_('Токен авторизации'), max_length=32, unique=True, null=True, blank=True, help_text=_('Токен для авторизации в боте'))
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

