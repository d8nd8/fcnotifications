from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import timedelta
from unfold.admin import ModelAdmin
from .models import Device, BatteryReport, Message, TelegramUser


def dashboard_callback(request, context):
    """Кастомный dashboard для Unfold"""
    now = timezone.now()
    yesterday = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)
    
    # Статистика устройств
    total_devices = Device.objects.count()
    online_devices = Device.objects.filter(last_seen__gte=yesterday).count()
    offline_devices = total_devices - online_devices
    
    # Статистика сообщений
    total_messages = Message.objects.count()
    today_messages = Message.objects.filter(created_at__gte=yesterday).count()
    week_messages = Message.objects.filter(created_at__gte=week_ago).count()
    
    # Статистика батареи
    recent_battery_reports = BatteryReport.objects.filter(created_at__gte=yesterday)
    low_battery_devices = recent_battery_reports.filter(battery_level__lt=20).count()
    
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
        'recent_messages': recent_messages,
    })
    
    return context


@admin.register(Device)
class DeviceAdmin(ModelAdmin):
    list_display = ['name', 'token_display', 'status_badge', 'last_seen', 'created_at']
    list_filter = ['created_at', 'last_seen']
    search_fields = ['name', 'external_id', 'token']
    readonly_fields = ['id', 'token', 'created_at', 'status_badge']
    list_per_page = 25
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()
    
    def token_display(self, obj):
        """Отображает токен с кнопкой копирования"""
        return format_html(
            '<code style="background: #f5f5f5; padding: 2px 6px; border-radius: 3px;">{}</code>',
            str(obj.token)[:8] + '...'
        )
    token_display.short_description = _('Токен')
    
    def status_badge(self, obj):
        """Показывает статус устройства"""
        if obj.last_seen:
            return format_html(
                '<span style="background: #4CAF50; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">🟢 Онлайн</span>'
            )
        else:
            return format_html(
                '<span style="background: #f44336; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">🔴 Офлайн</span>'
            )
    status_badge.short_description = _('Статус')


@admin.register(BatteryReport)
class BatteryReportAdmin(ModelAdmin):
    list_display = ['device', 'battery_level_display', 'date_created', 'created_at']
    list_filter = ['date_created', 'created_at', 'battery_level']
    search_fields = ['device__name', 'device__token']
    readonly_fields = ['id', 'created_at']
    list_per_page = 25
    
    def battery_level_display(self, obj):
        """Отображает уровень батареи с цветовой индикацией"""
        level = obj.battery_level
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
            '<span style="font-weight: bold; color: {};">{}%</span>'
            '</div>',
            level, color, color, level
        )
    battery_level_display.short_description = _('Уровень батареи')


@admin.register(Message)
class MessageAdmin(ModelAdmin):
    list_display = ['device', 'sender', 'text_preview', 'date_created', 'created_at']
    list_filter = ['date_created', 'created_at']
    search_fields = ['device__name', 'sender', 'text']
    readonly_fields = ['id', 'created_at', 'text_preview']
    list_per_page = 25
    
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


@admin.register(TelegramUser)
class TelegramUserAdmin(ModelAdmin):
    list_display = ['user_display', 'username', 'is_active', 'last_activity', 'created_at']
    list_filter = ['is_active', 'created_at', 'last_activity']
    search_fields = ['username', 'first_name', 'last_name', 'user_id']
    readonly_fields = ['id', 'user_id', 'created_at', 'last_activity']
    list_per_page = 25
    
    def user_display(self, obj):
        """Отображает информацию о пользователе"""
        name = f"{obj.first_name} {obj.last_name}".strip() or "Без имени"
        username = f"@{obj.username}" if obj.username else "Без username"
        return format_html(
            '<div><strong>{}</strong><br><small style="color: #666;">{}</small></div>',
            name, username
        )
    user_display.short_description = _('Пользователь')

