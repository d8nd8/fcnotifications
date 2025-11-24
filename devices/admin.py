from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpRequest
from datetime import timedelta
from unfold.admin import ModelAdmin
from unfold.decorators import action
from unfold.contrib.filters.admin import (
    RangeDateFilter,
    RelatedDropdownFilter,
)
from .models import Device, Message, TelegramUser, NotificationFilter, AuthToken, LogFile, DeviceStatus
import secrets
import string


def dashboard_callback(request, context):
    """Кастомный dashboard для Unfold"""
    now = timezone.now()
    yesterday = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)
    
    # Статистика устройств
    total_devices = Device.objects.count()
    
    # Определяем офлайн устройства по статусу: если последний DeviceStatus имеет network_available=False или status_level='ERROR'
    # Получаем последний статус для каждого устройства
    from django.db.models import OuterRef, Subquery
    
    latest_status = DeviceStatus.objects.filter(
        device=OuterRef('pk')
    ).order_by('-date_created')
    
    devices_with_status = Device.objects.annotate(
        latest_network_available=Subquery(
            latest_status.values('network_available')[:1]
        ),
        latest_status_level=Subquery(
            latest_status.values('status_level')[:1]
        )
    )
    
    # Устройство офлайн, если:
    # 1. У него нет DeviceStatus (latest_network_available is None)
    # 2. Или latest_network_available=False
    # 3. Или latest_status_level='ERROR'
    offline_devices = devices_with_status.filter(
        Q(latest_network_available__isnull=True) | 
        Q(latest_network_available=False) | 
        Q(latest_status_level='ERROR')
    ).count()
    
    online_devices = total_devices - offline_devices
    
    # Статистика сообщений
    total_messages = Message.objects.count()
    today_messages = Message.objects.filter(created_at__gte=yesterday).count()
    week_messages = Message.objects.filter(created_at__gte=week_ago).count()
    
    # Статистика батареи (из отчетов о статусе)
    recent_status_reports = DeviceStatus.objects.filter(created_at__gte=yesterday)
    low_battery_devices = recent_status_reports.filter(battery_level__lt=20).count()
    
    # Статистика зарядки
    charging_devices = recent_status_reports.filter(is_charging=True).values('device').distinct().count()
    
    # Статистика сети
    devices_with_network = recent_status_reports.filter(network_available=True).values('device').distinct().count()
    
    # Статистика логов
    total_logs = LogFile.objects.count()
    today_logs = LogFile.objects.filter(created_at__gte=yesterday).count()
    week_logs = LogFile.objects.filter(created_at__gte=week_ago).count()
    
    # Статистика статусов устройств
    success_status = recent_status_reports.filter(status_level='SUCCESS').count()
    attention_status = recent_status_reports.filter(status_level='ATTENTION').count()
    error_status = recent_status_reports.filter(status_level='ERROR').count()
    
    # Последние отчеты о статусе
    recent_status_qs = (
        DeviceStatus.objects.select_related("device")
        .order_by("-date_created")[:10]
    )
    recent_status = [
        {
            "device_name": s.device.name,
            "device_id": str(s.device.id),
            "status_level": s.status_level,
            "battery_level": s.battery_level,
            "is_charging": s.is_charging,
            "network_available": s.network_available,
            "reasons": s.reasons,
            "date_created": s.date_created,
        }
        for s in recent_status_qs
    ]
    
    # Последние сообщения (лог)
    recent_messages_qs = (
        Message.objects.select_related("device")
        .order_by("-date_created")[:10]
    )
    recent_messages = [
        {
            "device_name": m.device.name,
            "device_id": str(m.device.id),
            "sender": m.sender,
            "text": m.text,
            "date_created": m.date_created,
        }
        for m in recent_messages_qs
    ]
    
    # Последние логи
    recent_logs_qs = (
        LogFile.objects.select_related("device")
        .order_by("-date_created")[:5]
    )
    recent_logs = [
        {
            "device_name": l.device.name,
            "device_id": str(l.device.id),
            "file_name": l.file.name.split('/')[-1] if l.file else "No file",
            "file_url": l.file.url if l.file else None,
            "date_created": l.date_created,
        }
        for l in recent_logs_qs
    ]

    # Простая статистика для Unfold + данные для таблиц
    context.update({
        'title': '📱 FC Phones - Панель управления',
        'subtitle': 'Сервис алертов для мобильных устройств',
        'devices_total': total_devices,
        'devices_online': online_devices,
        'devices_offline': offline_devices,
        'messages_today': today_messages,
        'messages_week': week_messages,
        'low_battery_count': low_battery_devices,
        'charging_devices': charging_devices,
        'devices_with_network': devices_with_network,
        'logs_total': total_logs,
        'logs_today': today_logs,
        'logs_week': week_logs,
        'success_status': success_status,
        'attention_status': attention_status,
        'error_status': error_status,
        'recent_messages': recent_messages,
        'recent_logs': recent_logs,
        'recent_status': recent_status,
    })
    
    return context


@admin.register(Device)
class DeviceAdmin(ModelAdmin):
    list_display = ['id_display', 'name', 'token_display', 'last_seen']
    list_display_links = ['id_display']  # Ссылка на детали через ID
    list_filter = ['created_at', 'last_seen']
    search_fields = ['name', 'token']
    readonly_fields = ['id', 'token', 'created_at']
    list_per_page = 25
    actions_list = ["create_devices_action"]
    
    # Делаем поле name редактируемым в списке
    list_editable = ['name']
    
    @action(description=_("📱 Создать 10 устройств"), url_path="create-devices", permissions=["add"])
    def create_devices_action(self, request: HttpRequest):
        """Создает 10 новых устройств с уникальными токенами"""
        try:
            created_devices = []
            for i in range(10):
                device = Device.objects.create(
                    name=f"Устройство {i+1}"
                )
                created_devices.append(device)
            
            messages.success(
                request, 
                f'✅ Успешно создано 10 устройств! Токены сгенерированы автоматически.'
            )
            
        except Exception as e:
            messages.error(
                request, 
                f'❌ Ошибка при создании устройств: {str(e)}'
            )
        
        return redirect(reverse('admin:devices_device_changelist'))
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()
    
    def id_display(self, obj):
        """Отображает первые 8 символов ID как ссылку"""
        return format_html(
            '<span style="font-family: monospace; font-size: 12px; color: #6b7280;">{}</span>',
            str(obj.id)[:8] + '...'
        )
    id_display.short_description = _('ID')
    
    def token_display(self, obj):
        """Отображает токен (выделяемый для копирования)"""
        return format_html(
            '<code style="background: #374151; color: #f3f4f6; padding: 4px 8px; border-radius: 6px; font-family: monospace; font-size: 12px; border: 1px solid #4b5563; user-select: all; cursor: text;" title="Кликните для выделения, затем Ctrl+C для копирования">{}</code>',
            str(obj.token)
        )
    token_display.short_description = _('Токен')
    
    def status_badge(self, obj):
        """Показывает статус устройства на основе последнего DeviceStatus"""
        # Получаем последний статус устройства
        latest_status = obj.status_reports.order_by('-date_created').first()
        
        if latest_status:
            # Устройство офлайн, если network_available=False или status_level='ERROR'
            if not latest_status.network_available or latest_status.status_level == 'ERROR':
                return format_html(
                    '<span style="background: #f44336; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">🔴 Офлайн</span>'
                )
            else:
                return format_html(
                    '<span style="background: #4CAF50; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">🟢 Онлайн</span>'
                )
        else:
            # Если нет статуса, считаем офлайн
            return format_html(
                '<span style="background: #f44336; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">🔴 Офлайн</span>'
            )
    status_badge.short_description = _('Статус')


# BatteryReportAdmin удален - функциональность перенесена в DeviceStatusAdmin


@admin.register(Message)
class MessageAdmin(ModelAdmin):
    list_display = ['device_name', 'sender', 'date_created_display', 'package_name', 'text_preview']
    list_filter = [
        ('device', RelatedDropdownFilter),  # Дропдаун фильтр по устройству (ForeignKey)
        ('date_created', RangeDateFilter),  # Unfold фильтр по дате
        'package_name',  # Дропдаун фильтр по имени пакета (CharField - стандартный Django фильтр показывает уникальные значения)
        'sender',
        'is_filtered',
    ]
    search_fields = ['text', 'device__name']
    readonly_fields = ['id', 'created_at', 'text_preview']
    list_per_page = 25
    list_filter_submit = True  # Добавляет кнопку "Применить" для фильтров
    actions_list = ['clear_all_messages']
    
    def device_name(self, obj):
        """Показывает только имя устройства"""
        return format_html(
            '<span style="display: inline-block; min-width: 150px; font-weight: 500;">{}</span>',
            obj.device.name
        )
    device_name.short_description = _('Устройство')
    device_name.admin_order_field = 'device__name'
    
    def date_created_display(self, obj):
        """Показывает дату получения SMS"""
        if not obj.date_created:
            return format_html(
                '<span style="font-family: monospace; font-size: 12px; color: #6b7280;">—</span>'
            )

        local_dt = timezone.localtime(obj.date_created)
        return format_html(
            '<span style="font-family: monospace; font-size: 12px; color: #6b7280;">{}</span>',
            local_dt.strftime('%d.%m.%Y %H:%M:%S')
        )
    date_created_display.short_description = _('Дата получения SMS')
    date_created_display.admin_order_field = 'date_created'
    
    def text_preview(self, obj):
        """Показывает превью текста сообщения"""
        text = obj.text
        if len(text) > 50:
            text = text[:50] + '...'
        return format_html(
            '<div style="max-width: 300px; overflow: hidden; text-overflow: ellipsis;">{}</div>',
            text
        )
    text_preview.short_description = _('Текст сообщения')
    
    @action(description=_("🗑️ Очистить все сообщения"), url_path="clear-all-messages", permissions=["delete"])
    def clear_all_messages(self, request: HttpRequest):
        """Удаляет все сообщения из базы данных"""
        try:
            count = Message.objects.count()
            Message.objects.all().delete()
            messages.success(request, f'✅ Успешно удалено {count} сообщений')
        except Exception as e:
            messages.error(request, f'❌ Ошибка при удалении сообщений: {str(e)}')
        
        return redirect(reverse('admin:devices_message_changelist'))


@admin.register(NotificationFilter)
class NotificationFilterAdmin(ModelAdmin):
    list_display = ['package_name', 'description', 'filter_type_badge', 'is_active_badge', 'created_at']
    list_filter = ['filter_type', 'is_active', 'created_at']
    search_fields = ['package_name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    list_per_page = 25
    
    def filter_type_badge(self, obj):
        """Показывает тип фильтра"""
        if obj.filter_type == 'blacklist':
            return format_html(
                '<span style="background: #f44336; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">🚫 Черный список</span>'
            )
        else:
            return format_html(
                '<span style="background: #4CAF50; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">✅ Белый список</span>'
            )
    filter_type_badge.short_description = _('Тип фильтра')
    
    def is_active_badge(self, obj):
        """Показывает статус активности"""
        if obj.is_active:
            return format_html(
                '<span style="background: #4CAF50; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">✅ Активен</span>'
            )
        else:
            return format_html(
                '<span style="background: #9e9e9e; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">❌ Неактивен</span>'
            )
    is_active_badge.short_description = _('Статус')


@admin.register(TelegramUser)
class TelegramUserAdmin(ModelAdmin):
    list_display = ['user_display', 'username', 'is_active', 'last_activity', 'created_at']
    list_filter = ['is_active', 'created_at', 'last_activity']
    search_fields = ['username', 'first_name', 'last_name', 'user_id']
    readonly_fields = ['id', 'user_id', 'created_at', 'last_activity']
    list_per_page = 25
    def get_queryset(self, request):
        return super().get_queryset(request)
    
    def user_display(self, obj):
        """Отображает информацию о пользователе"""
        name = f"{obj.first_name} {obj.last_name}".strip() or "Без имени"
        username = f"@{obj.username}" if obj.username else "Без username"
        return format_html(
            '<div><strong>{}</strong><br><small style="color: #666;">{}</small></div>',
            name, username
        )
    user_display.short_description = _('Пользователь')


@admin.register(AuthToken)
class AuthTokenAdmin(ModelAdmin):
    list_display = ['token', 'is_used_display', 'used_by_display', 'created_at', 'used_at']
    list_filter = ['is_used', 'created_at', 'used_at']
    search_fields = ['token', 'used_by__username', 'used_by__first_name']
    readonly_fields = ['id', 'created_at', 'used_at']
    list_per_page = 25
    actions_list = ['generate_token']
    
    def is_used_display(self, obj):
        """Отображает статус использования токена"""
        if obj.is_used:
            return format_html(
                '<span style="background: #4caf50; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">✅ Использован</span>'
            )
        else:
            return format_html(
                '<span style="background: #ff9800; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">⏳ Не использован</span>'
            )
    is_used_display.short_description = _('Статус')
    
    def used_by_display(self, obj):
        """Отображает пользователя, использовавшего токен"""
        if obj.used_by:
            return format_html(
                '<div><strong>{}</strong><br><small style="color: #666;">@{}</small></div>',
                f"{obj.used_by.first_name} {obj.used_by.last_name}".strip() or "Без имени",
                obj.used_by.username or "Без username"
            )
        return "—"
    used_by_display.short_description = _('Использован пользователем')
    
    @action(description=_("🔑 Сгенерировать токен"), url_path="generate-token", permissions=["add"])
    def generate_token(self, request):
        """Генерация одного токена авторизации"""
        # Генерируем уникальный токен
        while True:
            token = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(16))
            
            # Проверяем, что токен уникален
            if not AuthToken.objects.filter(token=token).exists():
                break
        
        # Создаем токен
        AuthToken.objects.create(token=token)
        
        messages.success(request, f'Токен сгенерирован: {token}')
        return redirect(reverse('admin:devices_authtoken_changelist'))


@admin.register(LogFile)
class LogFileAdmin(ModelAdmin):
    list_display = ['device_name', 'file', 'date_created']
    list_filter = ['date_created', 'device']
    search_fields = ['device__name', 'file']
    readonly_fields = ['id', 'created_at', 'device_name']
    list_per_page = 25
    
    def device_name(self, obj):
        """Показывает название устройства"""
        return obj.device.name
    device_name.short_description = _('Устройство')


@admin.register(DeviceStatus)
class DeviceStatusAdmin(ModelAdmin):
    list_display = ['device_name', 'status_badge', 'battery_level_display', 'is_charging_badge', 
                   'network_available_badge', 'app_version_display', 
                   'android_version_display', 'device_model', 'date_created']
    list_filter = ['status_level', 'is_charging', 'network_available', 'date_created', 'created_at', 
                   'device_model', 'app_version', 'android_version']
    search_fields = ['device__name', 'device__token', 'app_version', 'android_version', 'device_model']
    readonly_fields = ['id', 'created_at', 'reasons_display', 'timestamp_display', 'last_notification_display']
    list_per_page = 25
    ordering = ['-date_created']
    
    def device_name(self, obj):
        """Показывает только имя устройства"""
        return format_html(
            '<span style="display: inline-block; min-width: 150px; font-weight: 500;">{}</span>',
            obj.device.name
        )
    device_name.short_description = _('Устройство')
    device_name.admin_order_field = 'device__name'
    
    # Группировка полей в детальной странице
    fieldsets = (
        ('📱 Информация об устройстве', {
            'fields': ('device', 'device_model', 'app_version', 'android_version')
        }),
        ('📊 Статус и причины', {
            'fields': ('status_level', 'reasons_display')
        }),
        ('🔋 Состояние батареи', {
            'fields': ('battery_level', 'is_charging')
        }),
        ('🌐 Сетевая информация', {
            'fields': ('network_available', 'unsent_notifications', 'last_notification_display')
        }),
        ('⏰ Временные метки', {
            'fields': ('timestamp_display', 'date_created', 'created_at')
        }),
        ('🔧 Техническая информация', {
            'fields': ('id',),
            'classes': ('collapse',)
        })
    )
    
    def status_badge(self, obj):
        """Показывает только код статуса"""
        status_colors = {
            'SUCCESS': '#4CAF50',  # Зеленый
            'ATTENTION': '#FF9800',  # Оранжевый
            'ERROR': '#f44336'  # Красный
        }
        status_icons = {
            'SUCCESS': '✅',
            'ATTENTION': '⚠️',
            'ERROR': '❌'
        }
        
        color = status_colors.get(obj.status_level, '#9e9e9e')
        icon = status_icons.get(obj.status_level, '❓')
        
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: bold; white-space: nowrap;">{} {}</span>',
            color, icon, obj.status_level
        )
    status_badge.short_description = _('Статус')
    
    def battery_level_display(self, obj):
        """Отображает уровень батареи с цветовой индикацией"""
        level = obj.battery_level
        charging_icon = '🔌' if obj.is_charging else '🔋'
        
        if level > 50:
            color = '#4CAF50'  # Зеленый
        elif level > 20:
            color = '#FF9800'  # Оранжевый
        else:
            color = '#f44336'  # Красный
            
        return format_html(
            '<div style="display: flex; align-items: center;">'
            '<div style="width: 60px; background: #e0e0e0; height: 8px; border-radius: 4px; margin-right: 8px;">'
            '<div style="width: {}%; background: {}; height: 100%; border-radius: 4px;"></div>'
            '</div>'
            '<span style="font-weight: bold; color: {};">{}% {}</span>'
            '</div>',
            level, color, color, level, charging_icon
        )
    battery_level_display.short_description = _('Батарея')
    
    def is_charging_badge(self, obj):
        """Показывает статус зарядки"""
        if obj.is_charging:
            return format_html(
                '<span style="background: #4CAF50; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; white-space: nowrap;">🔌 Заряжается</span>'
            )
        else:
            return format_html(
                '<span style="background: #9e9e9e; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; white-space: nowrap;">🔋 Не заряжается</span>'
            )
    is_charging_badge.short_description = _('Зарядка')
    
    def network_available_badge(self, obj):
        """Показывает статус сети"""
        if obj.network_available:
            return format_html(
                '<span style="background: #4CAF50; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; white-space: nowrap;">🌐 Онлайн</span>'
            )
        else:
            return format_html(
                '<span style="background: #f44336; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; white-space: nowrap;">❌ Офлайн</span>'
            )
    network_available_badge.short_description = _('Сеть')
    
    def reasons_display(self, obj):
        """Показывает причины статуса в читаемом виде"""
        if not obj.reasons:
            return "Нет причин"
        
        reasons_html = '<ul style="margin: 0; padding-left: 20px;">'
        for reason in obj.reasons:
            reasons_html += f'<li style="margin-bottom: 4px;">{reason}</li>'
        reasons_html += '</ul>'
        
        return format_html(reasons_html)
    reasons_display.short_description = _('Причины статуса')
    
    def timestamp_display(self, obj):
        """Показывает timestamp в читаемом виде"""
        from datetime import datetime
        try:
            dt = datetime.fromtimestamp(obj.timestamp / 1000)
            return dt.strftime('%d.%m.%Y %H:%M:%S')
        except (ValueError, TypeError):
            return "Неверный timestamp"
    timestamp_display.short_description = _('Время отчёта')
    
    def app_version_display(self, obj):
        """Показывает версию приложения"""
        if obj.app_version:
            return format_html(
                '<span style="background: #e3f2fd; color: #1976d2; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-family: monospace;">{}</span>',
                obj.app_version
            )
        return "—"
    app_version_display.short_description = _('Версия приложения')
    
    def android_version_display(self, obj):
        """Показывает версию Android"""
        if obj.android_version:
            return format_html(
                '<span style="background: #e8f5e8; color: #2e7d32; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-family: monospace; white-space: nowrap;">{}</span>',
                obj.android_version
            )
        return "—"
    android_version_display.short_description = _('Android версия')
    
    def last_notification_display(self, obj):
        """Показывает время последнего уведомления"""
        if obj.last_notification_timestamp:
            return format_html(
                '<span style="color: #666; font-size: 12px;">{}</span>',
                obj.last_notification_timestamp.strftime('%d.%m.%Y %H:%M:%S')
            )
        return format_html(
            '<span style="color: #999; font-style: italic;">Нет данных</span>'
        )
    last_notification_display.short_description = _('Последнее уведомление')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('device')

