# Анализ новых данных диагностики

## 📊 Резюме

Новый endpoint `POST /mobile/diagnostics/batch` с моделями `DiagnosticEvent`, `DeviceStateSnapshot` и `MetricsSnapshot` предоставляет **значительно расширенные возможности** для мониторинга и диагностики устройств по сравнению с текущим `SimpleBatteryReportView`.

---

## 🔍 Что мы получаем сейчас (текущий endpoint)

### Текущие данные (`SimpleBatteryReportView`):
- ✅ Батарея: уровень, статус зарядки
- ✅ Сеть: доступность интернета
- ✅ Уведомления: количество неотправленных, время последнего
- ✅ Устройство: версия приложения, версия Android, модель
- ✅ Статус: автоматический расчет SUCCESS/ATTENTION/ERROR

---

## 🚀 Что мы получим с новыми данными

### 1. **Расширенный снимок состояния устройства** (`DeviceStateSnapshot`)

#### Новые данные о сети:
- `isWifi` / `isMobileData` - тип подключения
- `networkType` - детальный тип сети

#### Новые данные о системе Android:
- `screenOn` - экран включен/выключен
- `isDoze` - режим энергосбережения
- `isBatteryOptimized` - оптимизация батареи
- `isBackgroundRestricted` - ограничения фоновой работы
- `storageAvailable` - доступность хранилища
- `ramLow` - низкая память
- `cpuLoadPercent` - загрузка CPU

#### Новые данные о сервисе:
- `serviceBound` - сервис привязан
- `serviceRunning` - сервис запущен
- `workerRunning` - воркер запущен
- `hasNotifPermission` - разрешение на уведомления
- `queueSize` - размер очереди
- `uploadQueueSize` - размер очереди загрузки
- `workerPendingTasks` - задачи воркера в ожидании

#### Новые данные о производительности:
- `lastCallbackTimestamp` - время последнего колбэка
- `lastUploadTimestamp` - время последней загрузки
- `appStartTimestamp` - время запуска приложения
- `uptimeMs` - время работы приложения
- `avgQueueInsertLatencyMs` - средняя задержка вставки в очередь
- `avgProcessingLatencyMs` - средняя задержка обработки

### 2. **Метрики производительности** (`MetricsSnapshot`)

#### Агрегированные счетчики:
- `totalCallbacksReceived` - всего получено колбэков
- `totalEventsSent` - всего отправлено событий
- `totalRetries` - всего повторных попыток
- `totalServiceRestarts` - всего перезапусков сервиса

#### Временные метрики:
- `avgCallbackIntervalMs` - средний интервал между колбэками
- `callbackGapMs` - разрыв между колбэками
- `avgUploadLatencyMs` - средняя задержка загрузки

#### Метрики надежности:
- `failuresSinceLastRecovery` - ошибок с последнего восстановления

### 3. **Структурированные события диагностики** (`DiagnosticEvent`)

#### Классификация событий:
- `eventCode` - код события (строка)
- `eventSeverity` - уровень серьезности: INFO, WARNING, ERROR, CRITICAL
- `component` - компонент: APP, NOTIF_SERVICE, WORKER, NETWORK, SYSTEM
- `pipelineStage` - этап пайплайна: RECEIVE, STORE, QUEUE, SEND, UPLOAD

#### Контекст и отладка:
- `context` - произвольные данные (Map<String, Any?>)
- `thread` - имя потока
- `attempt` - номер попытки
- `flowId` - ID потока обработки

#### Пакетная загрузка:
- Множественные события в одном запросе
- Возможность отслеживать последовательность событий

---

## 💡 Возможности, которые открываются

### 1. **Детальная диагностика проблем**

#### Проблемы с сетью:
- Различать WiFi и мобильный интернет
- Отслеживать переключения между типами сети
- Анализировать влияние типа сети на задержки

#### Проблемы с батареей:
- Режим Doze и оптимизация батареи
- Влияние состояния экрана на работу
- Корреляция между зарядом и производительностью

#### Проблемы с производительностью:
- Задержки в очереди и обработке
- Загрузка CPU
- Низкая память (RAM)
- Время работы приложения (uptime)

### 2. **Мониторинг компонентов системы**

#### Отслеживание по компонентам:
- **APP** - проблемы в основном приложении
- **NOTIF_SERVICE** - проблемы в сервисе уведомлений
- **WORKER** - проблемы в фоновом воркере
- **NETWORK** - проблемы с сетью
- **SYSTEM** - системные проблемы

#### Отслеживание по этапам пайплайна:
- **RECEIVE** - получение уведомлений
- **STORE** - сохранение в БД
- **QUEUE** - постановка в очередь
- **SEND** - отправка на сервер
- **UPLOAD** - загрузка данных

### 3. **Анализ производительности**

#### Метрики для анализа:
- Средние задержки обработки
- Количество повторных попыток
- Частота перезапусков сервиса
- Интервалы между колбэками
- Задержки загрузки

#### Выявление проблем:
- Высокие задержки в определенных этапах
- Частые перезапуски сервиса
- Большое количество повторных попыток
- Аномальные интервалы между событиями

### 4. **Пакетная обработка событий**

#### Преимущества:
- Эффективная передача множества событий
- Сохранение последовательности событий
- Меньше сетевых запросов
- Возможность анализа цепочек событий

### 5. **Контекстная диагностика**

#### Дополнительные данные:
- Произвольный контекст в каждом событии
- Информация о потоке выполнения
- Номер попытки для retry-логики
- Flow ID для отслеживания потоков

---

## 📈 Сравнение: Текущее vs Новое

| Аспект | Текущее | Новое |
|--------|---------|-------|
| **Данные о батарее** | Уровень, зарядка | + Doze, оптимизация, экран |
| **Данные о сети** | Доступность | + Тип (WiFi/Mobile), networkType |
| **Данные о сервисе** | Нет | + Статус сервиса, воркера, очереди |
| **Производительность** | Нет | + CPU, RAM, задержки, uptime |
| **Метрики** | Нет | + Счетчики, средние значения, интервалы |
| **События** | Нет | + Структурированные события с severity |
| **Компоненты** | Нет | + Разделение по компонентам |
| **Пайплайн** | Нет | + Отслеживание этапов обработки |
| **Пакетная загрузка** | Нет | + Множественные события в одном запросе |
| **Контекст** | Нет | + Произвольные данные, thread, attempt, flowId |

---

## 🎯 Рекомендации по использованию

### 1. **Создать новую модель данных**

```python
class DiagnosticEvent(models.Model):
    # Основные поля
    event_id = models.CharField(max_length=255, unique=True)
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    timestamp = models.BigIntegerField()
    
    # Классификация
    event_code = models.CharField(max_length=100)
    event_severity = models.CharField(max_length=20)  # INFO, WARNING, ERROR, CRITICAL
    component = models.CharField(max_length=50)  # APP, NOTIF_SERVICE, WORKER, NETWORK, SYSTEM
    pipeline_stage = models.CharField(max_length=50, null=True)  # RECEIVE, STORE, QUEUE, SEND, UPLOAD
    
    # Контекст
    context = models.JSONField(default=dict)
    thread = models.CharField(max_length=255, null=True)
    attempt = models.IntegerField(null=True)
    flow_id = models.CharField(max_length=255, null=True)
    
    # Снимки состояния (JSON)
    state_snapshot = models.JSONField(null=True)  # DeviceStateSnapshot
    metrics_snapshot = models.JSONField(null=True)  # MetricsSnapshot
    
    created_at = models.DateTimeField(auto_now_add=True)
```

### 2. **Использовать для улучшения расчета статуса**

Расширить `DeviceStatusCalculator` с учетом новых данных:
- Режим Doze → может влиять на задержки
- Оптимизация батареи → может блокировать фоновую работу
- Задержки обработки → индикатор проблем производительности
- Количество перезапусков → индикатор нестабильности

### 3. **Создать дашборд для анализа**

- Графики метрик производительности
- Фильтрация по компонентам и severity
- Анализ пайплайна (где задержки)
- Тренды по времени

### 4. **Алерты на основе событий**

- CRITICAL события → немедленное уведомление
- Частые ERROR в определенном компоненте
- Высокие задержки в пайплайне
- Аномальные метрики (много retries, перезапусков)

---

## 🗄️ Архитектура хранения данных и админка

### Рекомендация: Единая модель для всех диагностических данных

**Все поля и данные лучше формировать в новую модель** `DiagnosticEvent`, которая будет централизованно хранить всю диагностическую информацию. Это обеспечит:

1. ✅ **Единообразие** - все диагностические данные в одном месте
2. ✅ **Удобство запросов** - простой поиск и фильтрация
3. ✅ **Масштабируемость** - легко добавлять новые поля
4. ✅ **Производительность** - индексы на ключевых полях

### Предлагаемая модель данных

```python
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
        except:
            return str(self.timestamp)
```

### Админка Django с удобным экспортом

#### 1. **Отдельный раздел админки для диагностики**

Создать отдельный раздел админки с:
- Удобной фильтрацией по всем ключевым полям
- Группировкой событий
- Быстрым поиском
- Экспортом данных

```python
# devices/admin.py
# Админка адаптирована под django-unfold

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin  # Используем ModelAdmin из unfold
from unfold.decorators import action  # Декоратор для действий
from unfold.contrib.filters.admin import (
    RangeDateFilter,  # Фильтр по диапазону дат
    RelatedDropdownFilter,  # Дропдаун фильтр для ForeignKey
)
from .models import DiagnosticEvent
import csv
import json


@admin.register(DiagnosticEvent)
class DiagnosticEventAdmin(ModelAdmin):
    """
    Админка для диагностических событий с удобным экспортом (django-unfold)
    """
    list_display = [
        'event_code', 
        'severity_badge', 
        'component', 
        'device_link', 
        'timestamp_display',
        'pipeline_stage',
        'created_at'
    ]
    list_filter = [
        'event_severity',
        'component',
        'pipeline_stage',
        ('created_at', RangeDateFilter),  # Unfold фильтр по дате
        ('device', RelatedDropdownFilter),  # Unfold дропдаун фильтр по устройству
    ]
    search_fields = [
        'event_code',
        'event_id',
        'device__name',
        'device__token',
        'thread',
        'flow_id',
    ]
    readonly_fields = [
        'id',
        'event_id',
        'created_at',
        'state_snapshot_preview',
        'metrics_snapshot_preview',
        'context_preview',
    ]
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('event_id', 'device', 'timestamp', 'created_at')
        }),
        (_('Классификация'), {
            'fields': ('event_code', 'event_severity', 'component', 'pipeline_stage')
        }),
        (_('Контекст и отладка'), {
            'fields': ('context_preview', 'thread', 'attempt', 'flow_id')
        }),
        (_('Снимки состояния'), {
            'fields': ('state_snapshot_preview', 'metrics_snapshot_preview'),
            'classes': ('collapse',)
        }),
    )
    
    date_hierarchy = 'created_at'
    list_per_page = 25
    list_filter_submit = True  # Кнопка "Применить" для фильтров
    
    # Действия для экспорта (используем actions_list для Unfold)
    actions_list = [
        'export_to_csv_action',
        'export_to_json_action',
        'export_error_log_action',
        'export_device_diagnostics_action',
    ]
    
    def get_queryset(self, request):
        """Оптимизация запросов с select_related"""
        return super().get_queryset(request).select_related('device')
    
    def severity_badge(self, obj):
        """Цветной бейдж для severity"""
        colors = {
            'INFO': 'blue',
            'WARNING': 'orange',
            'ERROR': 'red',
            'CRITICAL': 'darkred',
        }
        color = colors.get(obj.event_severity, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.event_severity
        )
    severity_badge.short_description = _('Уровень')
    
    def device_link(self, obj):
        """Ссылка на устройство"""
        url = reverse('admin:devices_device_change', args=[obj.device.pk])
        return format_html('<a href="{}">{}</a>', url, obj.device.name)
    device_link.short_description = _('Устройство')
    
    def timestamp_display(self, obj):
        """Читаемое отображение timestamp"""
        return obj.get_timestamp_display()
    timestamp_display.short_description = _('Время события')
    
    def state_snapshot_preview(self, obj):
        """Превью снимка состояния"""
        if not obj.state_snapshot:
            return '-'
        import json
        return format_html(
            '<pre style="max-height: 300px; overflow: auto;">{}</pre>',
            json.dumps(obj.state_snapshot, indent=2, ensure_ascii=False)
        )
    state_snapshot_preview.short_description = _('Снимок состояния')
    
    def metrics_snapshot_preview(self, obj):
        """Превью снимка метрик"""
        if not obj.metrics_snapshot:
            return '-'
        import json
        return format_html(
            '<pre style="max-height: 300px; overflow: auto;">{}</pre>',
            json.dumps(obj.metrics_snapshot, indent=2, ensure_ascii=False)
        )
    metrics_snapshot_preview.short_description = _('Снимок метрик')
    
    def context_preview(self, obj):
        """Превью контекста"""
        if not obj.context:
            return '-'
        import json
        return format_html(
            '<pre style="max-height: 200px; overflow: auto;">{}</pre>',
            json.dumps(obj.context, indent=2, ensure_ascii=False)
        )
    context_preview.short_description = _('Контекст')
    
    # Действия экспорта (используем @action декоратор для Unfold)
    # Действия регистрируются через actions_list в начале класса
    
    @action(description=_("📊 Экспортировать в CSV"), url_path="export-csv", permissions=["view"])
    def export_to_csv_action(self, request: HttpRequest):
        """Экспорт выбранных событий в CSV"""
        # Получаем выбранные объекты из GET параметров
        selected_ids = request.GET.getlist('_selected_action')
        if not selected_ids:
            messages.warning(request, _('Не выбрано ни одного события для экспорта'))
            return redirect(reverse('admin:devices_diagnosticevent_changelist'))
        
        queryset = DiagnosticEvent.objects.filter(id__in=selected_ids).select_related('device')
        
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="diagnostic_events.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Event ID', 'Device', 'Timestamp', 'Event Code', 'Severity',
            'Component', 'Pipeline Stage', 'Thread', 'Attempt', 'Flow ID'
        ])
        
        for event in queryset:
            writer.writerow([
                event.event_id,
                event.device.name,
                event.get_timestamp_display(),
                event.event_code,
                event.event_severity,
                event.component,
                event.pipeline_stage or '',
                event.thread or '',
                event.attempt or '',
                event.flow_id or '',
            ])
        
        messages.success(request, _('Экспорт в CSV выполнен успешно'))
        return response
    
    @action(description=_("📄 Экспортировать в JSON"), url_path="export-json", permissions=["view"])
    def export_to_json_action(self, request: HttpRequest):
        """Экспорт выбранных событий в JSON"""
        selected_ids = request.GET.getlist('_selected_action')
        if not selected_ids:
            messages.warning(request, _('Не выбрано ни одного события для экспорта'))
            return redirect(reverse('admin:devices_diagnosticevent_changelist'))
        
        queryset = DiagnosticEvent.objects.filter(id__in=selected_ids).select_related('device')
        
        events_data = []
        for event in queryset:
            events_data.append({
                'event_id': event.event_id,
                'device': event.device.name,
                'device_token': str(event.device.token),
                'timestamp': event.timestamp,
                'timestamp_display': event.get_timestamp_display(),
                'event_code': event.event_code,
                'event_severity': event.event_severity,
                'component': event.component,
                'pipeline_stage': event.pipeline_stage,
                'thread': event.thread,
                'attempt': event.attempt,
                'flow_id': event.flow_id,
                'context': event.context,
                'state_snapshot': event.state_snapshot,
                'metrics_snapshot': event.metrics_snapshot,
                'created_at': event.created_at.isoformat(),
            })
        
        response = HttpResponse(
            json.dumps(events_data, indent=2, ensure_ascii=False),
            content_type='application/json; charset=utf-8'
        )
        response['Content-Disposition'] = 'attachment; filename="diagnostic_events.json"'
        messages.success(request, _('Экспорт в JSON выполнен успешно'))
        return response
    
    @action(description=_("🚨 Экспортировать лог ошибок"), url_path="export-error-log", permissions=["view"])
    def export_error_log_action(self, request: HttpRequest):
        """
        Экспорт ошибок в удобный читаемый лог для разработчика
        Фильтрует только ERROR и CRITICAL события
        """
        selected_ids = request.GET.getlist('_selected_action')
        if not selected_ids:
            messages.warning(request, _('Не выбрано ни одного события для экспорта'))
            return redirect(reverse('admin:devices_diagnosticevent_changelist'))
        
        queryset = DiagnosticEvent.objects.filter(id__in=selected_ids).select_related('device')
        error_events = queryset.filter(
            event_severity__in=['ERROR', 'CRITICAL']
        ).order_by('device', 'timestamp')
        
        if not error_events.exists():
            messages.warning(request, _('Нет ошибок для экспорта среди выбранных событий'))
            return redirect(reverse('admin:devices_diagnosticevent_changelist'))
        
        response = HttpResponse(content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="error_log.txt"'
        
        lines = []
        lines.append("=" * 80)
        lines.append("ОТЧЕТ ОБ ОШИБКАХ - ДИАГНОСТИЧЕСКИЕ СОБЫТИЯ")
        lines.append("=" * 80)
        lines.append(f"Дата создания: {timezone.now().strftime('%d.%m.%Y %H:%M:%S')}")
        lines.append(f"Всего ошибок: {error_events.count()}")
        lines.append("=" * 80)
        lines.append("")
        
        current_device = None
        for event in error_events:
            # Разделитель между устройствами
            if current_device != event.device:
                if current_device is not None:
                    lines.append("")
                current_device = event.device
                lines.append(f"\n{'=' * 80}")
                lines.append(f"УСТРОЙСТВО: {event.device.name} (Token: {event.device.token})")
                lines.append(f"{'=' * 80}")
                lines.append("")
            
            # Информация о событии
            lines.append(f"[{event.get_timestamp_display()}] {event.event_severity} - {event.event_code}")
            lines.append(f"  Компонент: {event.component}")
            if event.pipeline_stage:
                lines.append(f"  Этап пайплайна: {event.pipeline_stage}")
            if event.thread:
                lines.append(f"  Поток: {event.thread}")
            if event.attempt:
                lines.append(f"  Попытка: {event.attempt}")
            if event.flow_id:
                lines.append(f"  Flow ID: {event.flow_id}")
            
            # Контекст
            if event.context:
                lines.append("  Контекст:")
                for key, value in event.context.items():
                    lines.append(f"    {key}: {value}")
            
            # Снимок состояния (только ключевые поля)
            if event.state_snapshot:
                state = event.state_snapshot
                lines.append("  Состояние устройства:")
                if state.get('batteryLevel') is not None:
                    lines.append(f"    Батарея: {state['batteryLevel']}% {'(заряжается)' if state.get('isCharging') else ''}")
                if state.get('isNetworkAvailable') is not None:
                    lines.append(f"    Сеть: {'доступна' if state['isNetworkAvailable'] else 'недоступна'}")
                if state.get('networkType'):
                    lines.append(f"    Тип сети: {state['networkType']}")
                if state.get('serviceRunning') is not None:
                    lines.append(f"    Сервис: {'запущен' if state['serviceRunning'] else 'остановлен'}")
                if state.get('workerRunning') is not None:
                    lines.append(f"    Воркер: {'запущен' if state['workerRunning'] else 'остановлен'}")
                if state.get('queueSize') is not None:
                    lines.append(f"    Размер очереди: {state['queueSize']}")
            
            # Снимок метрик
            if event.metrics_snapshot:
                metrics = event.metrics_snapshot
                lines.append("  Метрики:")
                if metrics.get('totalRetries') is not None:
                    lines.append(f"    Всего повторных попыток: {metrics['totalRetries']}")
                if metrics.get('totalServiceRestarts') is not None:
                    lines.append(f"    Всего перезапусков сервиса: {metrics['totalServiceRestarts']}")
                if metrics.get('failuresSinceLastRecovery') is not None:
                    lines.append(f"    Ошибок с последнего восстановления: {metrics['failuresSinceLastRecovery']}")
            
            lines.append("")
            lines.append("-" * 80)
            lines.append("")
        
        response.write("\n".join(lines))
        messages.success(request, _('Лог ошибок экспортирован успешно'))
        return response
    
    @action(description=_("📱 Экспортировать отчет по устройствам"), url_path="export-device-diagnostics", permissions=["view"])
    def export_device_diagnostics_action(self, request: HttpRequest):
        """
        Экспорт всех диагностических данных по выбранным устройствам
        Группирует события по устройствам и создает полный отчет
        """
        selected_ids = request.GET.getlist('_selected_action')
        if not selected_ids:
            messages.warning(request, _('Не выбрано ни одного события для экспорта'))
            return redirect(reverse('admin:devices_diagnosticevent_changelist'))
        
        queryset = DiagnosticEvent.objects.filter(id__in=selected_ids).select_related('device')
        devices = set(event.device for event in queryset)
        
        if not devices:
            messages.warning(request, _('Нет данных для экспорта'))
            return redirect(reverse('admin:devices_diagnosticevent_changelist'))
        
        response = HttpResponse(content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="device_diagnostics.txt"'
        
        lines = []
        lines.append("=" * 80)
        lines.append("ПОЛНЫЙ ОТЧЕТ ПО ДИАГНОСТИКЕ УСТРОЙСТВ")
        lines.append("=" * 80)
        lines.append(f"Дата создания: {timezone.now().strftime('%d.%m.%Y %H:%M:%S')}")
        lines.append(f"Количество устройств: {len(devices)}")
        lines.append("=" * 80)
        lines.append("")
        
        for device in devices:
            device_events = queryset.filter(device=device).order_by('timestamp')
            
            lines.append(f"\n{'=' * 80}")
            lines.append(f"УСТРОЙСТВО: {device.name}")
            lines.append(f"Token: {device.token}")
            lines.append(f"Последний раз онлайн: {device.last_seen.strftime('%d.%m.%Y %H:%M:%S') if device.last_seen else 'Никогда'}")
            lines.append(f"Всего событий: {device_events.count()}")
            lines.append(f"{'=' * 80}")
            lines.append("")
            
            # Статистика по severity
            severity_stats = {}
            for event in device_events:
                severity_stats[event.event_severity] = severity_stats.get(event.event_severity, 0) + 1
            
            if severity_stats:
                lines.append("Статистика по уровням серьезности:")
                for severity, count in sorted(severity_stats.items()):
                    lines.append(f"  {severity}: {count}")
                lines.append("")
            
            # Статистика по компонентам
            component_stats = {}
            for event in device_events:
                component_stats[event.component] = component_stats.get(event.component, 0) + 1
            
            if component_stats:
                lines.append("Статистика по компонентам:")
                for component, count in sorted(component_stats.items()):
                    lines.append(f"  {component}: {count}")
                lines.append("")
            
            # Последние события (первые 20)
            lines.append("Последние события:")
            for event in device_events[:20]:
                lines.append(f"  [{event.get_timestamp_display()}] {event.event_severity} - {event.event_code} ({event.component})")
            
            if device_events.count() > 20:
                lines.append(f"  ... и еще {device_events.count() - 20} событий")
            
            lines.append("")
        
        response.write("\n".join(lines))
        messages.success(request, _('Отчет по устройствам экспортирован успешно'))
        return response
```

#### 2. **Преимущества такого подхода**

✅ **Централизованное хранение** - все диагностические данные в одной модели  
✅ **Удобная админка (django-unfold)** - современный интерфейс с фильтрами, поиском, группировкой  
✅ **Гибкий экспорт** - CSV, JSON, читаемые логи через действия Unfold  
✅ **Автоматизация** - экспорт ошибок для разработчика одним кликом  
✅ **Масштабируемость** - легко добавлять новые типы экспорта через `@action` декоратор  
✅ **Производительность** - индексы на ключевых полях для быстрого поиска  
✅ **Интеграция с Unfold** - использует `RangeDateFilter` и `RelatedDropdownFilter` для удобной фильтрации  

#### 3. **Сценарии использования**

**Сбор данных по устройствам:**
- Фильтр по устройству → экспорт всех событий
- Группировка по времени, компонентам, severity
- Анализ трендов и паттернов

**Обработка ошибок:**
- Фильтр ERROR/CRITICAL → экспорт в читаемый лог
- Автоматическая отправка разработчику (можно добавить email/Telegram)
- Контекст и состояние устройства в момент ошибки

**Отладка:**
- Поиск по flow_id для отслеживания потока обработки
- Фильтр по компоненту для локализации проблемы
- Анализ метрик производительности

---

## ✅ Выводы

Новые данные предоставляют **полноценную систему диагностики** вместо простого мониторинга статуса:

1. ✅ **Детальная диагностика** - понимание причин проблем на уровне компонентов
2. ✅ **Производительность** - метрики для оптимизации
3. ✅ **Структурированность** - классификация по severity, component, pipeline
4. ✅ **Масштабируемость** - пакетная загрузка событий
5. ✅ **Гибкость** - произвольный контекст для расширения

### 🎯 Ключевые рекомендации по реализации:

1. **Единая модель `DiagnosticEvent`** - все диагностические данные в одной модели для удобства управления и запросов

2. **Отдельный раздел админки** - специализированная админка с:
   - Удобными фильтрами по всем ключевым полям
   - Быстрым поиском и группировкой
   - Цветными индикаторами severity
   - Превью JSON данных

3. **Множественные варианты экспорта**:
   - **CSV** - для анализа в Excel/Google Sheets
   - **JSON** - для программной обработки
   - **Читаемый лог ошибок** - для отправки разработчику (только ERROR/CRITICAL)
   - **Полный отчет по устройствам** - для сбора всех данных по устройству

4. **Автоматизация сбора данных**:
   - Фильтрация по устройствам для сбора всех событий
   - Группировка по времени, компонентам, severity
   - Статистика по устройствам

5. **Удобная обработка ошибок**:
   - Экспорт ошибок в читаемый формат одним кликом
   - Включение контекста и состояния устройства
   - Возможность автоматической отправки разработчику

**Рекомендация**: Реализовать новую модель `DiagnosticEvent` с полнофункциональной админкой и экспортом данных. Это обеспечит удобный сбор данных по устройствам и быструю обработку ошибок для разработчиков.
