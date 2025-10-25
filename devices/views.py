from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Device, BatteryReport, Message, LogFile, DeviceStatus
from .serializers import DeviceSerializer, MessageSerializer, LogFileSerializer, DeviceStatusSerializer
from .notifications import notify
from .notification_filter import NotificationFilterService
from .status_calculator import DeviceStatusCalculator


class DeviceView(APIView):
    """
    Получение информации об устройстве
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="📱 Получить информацию об устройстве",
        operation_description="""
        Возвращает подробную информацию об аутентифицированном устройстве.
        
        **Аутентификация**: Требуется заголовок `X-TOKEN` с токеном устройства.
        
        **Использование**: 
        - Получение данных устройства для отображения в мобильном приложении
        - Проверка статуса регистрации устройства
        - Получение последнего времени активности
        """,
        tags=['Устройства'],
        responses={
            200: openapi.Response(
                description="Информация об устройстве успешно получена",
                schema=DeviceSerializer,
                examples={
                    "application/json": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "external_id": "device_12345",
                        "token": "abc123def456ghi789",
                        "name": "Мой iPhone",
                        "last_seen": "2024-01-15T14:30:25Z",
                        "created_at": "2024-01-01T10:00:00Z"
                    }
                }
            ),
            401: openapi.Response(
                description="Неверный или отсутствующий токен аутентификации",
                examples={
                    "application/json": {
                        "detail": "Authentication credentials were not provided."
                    }
                }
            )
        },
        manual_parameters=[
            openapi.Parameter(
                'X-TOKEN',
                openapi.IN_HEADER,
                description="Токен аутентификации устройства",
                type=openapi.TYPE_STRING,
                required=True,
                example="abc123def456ghi789"
            )
        ]
    )
    def get(self, request):
        device = request.user  # This will be the Device instance from XTokenAuthentication
        serializer = DeviceSerializer(device)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SimpleBatteryReportView(APIView):
    """
    Расширенная отправка отчета о статусе устройства (без аутентификации)
    """
    permission_classes = []  # Убираем требование аутентификации
    
    @swagger_auto_schema(
        operation_summary="📊 Отправить расширенный отчет о статусе устройства",
        operation_description="""
        Расширенная отправка отчета о статусе устройства без аутентификации.
        Поддерживает как простую отправку только батареи, так и полный отчет о статусе.
        
        **Использование**:
        - Отправка полного отчета о статусе устройства каждые 15 минут
        - Быстрая отправка данных о батарее (обратная совместимость)
        - Мониторинг состояния устройства
        
        **Обязательные параметры**:
        - `token` - токен устройства
        - `battery_level` - уровень батареи 0-100
        
        **Дополнительные параметры для полного отчета**:
        - `is_charging` - заряжается ли устройство
        - `network_available` - есть ли доступ к интернету
        - `unsent_notifications` - количество неотправленных уведомлений
        - `last_notification_timestamp` - время последнего уведомления
        - `timestamp` - время формирования отчёта (UNIX миллисекунды)
        - `app_version` - версия приложения
        - `android_version` - версия Android
        - `device_model` - модель устройства
        - `reasons` - список причин статуса (опционально, если не указано - рассчитывается автоматически)
        - `status_level` - общий статус устройства SUCCESS/ATTENTION/ERROR (опционально, если не указано - рассчитывается автоматически)
        
        **Ответ содержит все поля**:
        - `device_id` - уникальный идентификатор устройства
        - `status_level` - общий статус устройства (SUCCESS, ATTENTION, ERROR)
        - `reasons` - список текстовых причин текущего состояния
        - `battery_level` - уровень заряда батареи (в процентах)
        - `is_charging` - заряжается ли устройство сейчас
        - `network_available` - есть ли доступ к интернету
        - `unsent_notifications` - количество неотправленных уведомлений
        - `last_notification_timestamp` - время последнего полученного уведомления
        - `timestamp` - время формирования отчёта (в миллисекундах UNIX)
        - `app_version` - версия приложения
        - `android_version` - версия операционной системы Android
        - `device_model` - модель устройства
        """,
        tags=['Мониторинг устройства'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['token', 'battery_level'],
            properties={
                'token': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Токен устройства',
                    example='6f4d3982-2a0c-460b-95d6-7daaaf2b6f39'
                ),
                'battery_level': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='Уровень заряда батареи в процентах (0-100)',
                    minimum=0,
                    maximum=100,
                    example=85
                ),
                'is_charging': openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description='Заряжается ли устройство сейчас',
                    example=True
                ),
                'network_available': openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description='Есть ли доступ к интернету',
                    example=True
                ),
                'unsent_notifications': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='Количество неотправленных уведомлений',
                    minimum=0,
                    example=0
                ),
                'last_notification_timestamp': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_DATETIME,
                    description='Время последнего полученного уведомления (ISO 8601)',
                    example='2024-01-15T14:30:25Z'
                ),
                'timestamp': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='Время формирования отчёта в миллисекундах UNIX',
                    example=1705327825000
                ),
                'app_version': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Версия мобильного приложения',
                    example='1.2.3'
                ),
                'android_version': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Версия операционной системы Android',
                    example='Android 14'
                ),
                'device_model': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Модель устройства',
                    example='Samsung Galaxy S23'
                ),
                'reasons': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description='Список текстовых причин текущего состояния (опционально, если не указано - рассчитывается автоматически)',
                    example=['Низкий уровень батареи', 'Нет доступа к интернету']
                ),
                'status_level': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['SUCCESS', 'ATTENTION', 'ERROR'],
                    description='Общий статус устройства (опционально, если не указано - рассчитывается автоматически)',
                    example='SUCCESS'
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Отчет о статусе устройства успешно отправлен",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Отчет о статусе устройства успешно отправлен",
                        "device_id": "550e8400-e29b-41d4-a716-446655440000",
                        "device_name": "Мой iPhone",
                        "status_level": "SUCCESS",
                        "reasons": ["Все системы работают нормально"],
                        "battery_level": 85,
                        "is_charging": True,
                        "network_available": True,
                        "unsent_notifications": 0,
                        "last_notification_timestamp": "2024-01-15T14:30:25Z",
                        "timestamp": 1705327825000,
                        "app_version": "1.2.3",
                        "android_version": "Android 14",
                        "device_model": "Samsung Galaxy S23",
                        "battery_report_id": "550e8400-e29b-41d4-a716-446655440001",
                        "status_report_id": "550e8400-e29b-41d4-a716-446655440002"
                    }
                }
            ),
            400: openapi.Response(
                description="Ошибка валидации данных",
                examples={
                    "application/json": {
                        "success": False,
                        "error": "Неверный уровень батареи"
                    }
                }
            ),
            404: openapi.Response(
                description="Устройство не найдено",
                examples={
                    "application/json": {
                        "success": False,
                        "error": "Устройство с таким токеном не найдено"
                    }
                }
            )
        }
    )
    def post(self, request):
        token = request.data.get('token')
        battery_level = request.data.get('battery_level')
        
        if not token:
            return Response({
                'success': False,
                'error': 'Токен устройства обязателен'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not battery_level or not isinstance(battery_level, int):
            return Response({
                'success': False,
                'error': 'Уровень батареи обязателен и должен быть числом'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if battery_level < 0 or battery_level > 100:
            return Response({
                'success': False,
                'error': 'Уровень батареи должен быть от 0 до 100'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            device = Device.objects.get(token=token)
        except Device.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Устройство с таким токеном не найдено'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Получаем дополнительные параметры с значениями по умолчанию
        is_charging = request.data.get('is_charging', False)
        network_available = request.data.get('network_available', True)
        unsent_notifications = request.data.get('unsent_notifications', 0)
        last_notification_timestamp = request.data.get('last_notification_timestamp')
        timestamp = request.data.get('timestamp', int(timezone.now().timestamp() * 1000))
        app_version = request.data.get('app_version', '')
        android_version = request.data.get('android_version', '')
        device_model = request.data.get('device_model', '')
        custom_reasons = request.data.get('reasons', [])
        custom_status_level = request.data.get('status_level')
        
        # Валидация status_level если передан
        if custom_status_level and custom_status_level not in ['SUCCESS', 'ATTENTION', 'ERROR']:
            return Response({
                'success': False,
                'error': 'status_level должен быть одним из: SUCCESS, ATTENTION, ERROR'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Парсим timestamp последнего уведомления если он передан
        if last_notification_timestamp:
            try:
                from django.utils.dateparse import parse_datetime
                last_notification_timestamp = parse_datetime(last_notification_timestamp)
            except (ValueError, TypeError):
                last_notification_timestamp = None
        
        # Рассчитываем статус устройства
        if custom_status_level and custom_reasons:
            # Если переданы и статус, и причины - используем их
            status_level = custom_status_level
            reasons = custom_reasons
        elif custom_status_level:
            # Если передан только статус - используем его, причины рассчитываем автоматически
            _, reasons = DeviceStatusCalculator.calculate_status_level(
                battery_level=battery_level,
                is_charging=is_charging,
                network_available=network_available,
                unsent_notifications=unsent_notifications,
                last_notification_timestamp=last_notification_timestamp
            )
            status_level = custom_status_level
        elif custom_reasons:
            # Если переданы только причины - используем их, статус рассчитываем автоматически
            status_level, _ = DeviceStatusCalculator.calculate_status_level(
                battery_level=battery_level,
                is_charging=is_charging,
                network_available=network_available,
                unsent_notifications=unsent_notifications,
                last_notification_timestamp=last_notification_timestamp
            )
            reasons = custom_reasons
        else:
            # Если ничего не передано - рассчитываем автоматически
            status_level, reasons = DeviceStatusCalculator.calculate_status_level(
                battery_level=battery_level,
                is_charging=is_charging,
                network_available=network_available,
                unsent_notifications=unsent_notifications,
                last_notification_timestamp=last_notification_timestamp
            )
        
        # Создаем отчет о батарее (для обратной совместимости)
        battery_report = BatteryReport.objects.create(
            device=device,
            battery_level=battery_level
        )
        
        # Создаем расширенный отчет о статусе устройства
        device_status = DeviceStatus.objects.create(
            device=device,
            status_level=status_level,
            reasons=reasons,
            battery_level=battery_level,
            is_charging=is_charging,
            network_available=network_available,
            unsent_notifications=unsent_notifications,
            last_notification_timestamp=last_notification_timestamp,
            timestamp=timestamp,
            app_version=app_version,
            android_version=android_version,
            device_model=device_model
        )
        
        # Обновляем last_seen устройства
        device.last_seen = timezone.now()
        device.save(update_fields=['last_seen'])
        
        # Отправляем уведомление в Telegram если статус требует внимания
        if status_level in ['ATTENTION', 'ERROR']:
            status_display = DeviceStatusCalculator.get_status_display(status_level)
            notification_text = f"📊 <b>СТАТУС УСТРОЙСТВА</b>\n\n"
            notification_text += f"📱 Устройство: {device.name}\n"
            notification_text += f"⏰ Время: {timezone.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
            notification_text += f"🔋 Батарея: {battery_level}% {'🔌' if is_charging else '🔋'}\n"
            notification_text += f"🌐 Интернет: {'✅' if network_available else '❌'}\n"
            notification_text += f"📨 Неотправленных: {unsent_notifications}\n"
            notification_text += f"📊 Статус: {status_display}\n\n"
            notification_text += f"⚠️ <b>Причины:</b>\n"
            for reason in reasons:
                notification_text += f"• {reason}\n"
            
            # TODO: Move to Celery for async processing
            notify(notification_text)
        
        return Response({
            'success': True,
            'message': 'Отчет о статусе устройства успешно отправлен',
            'device_id': str(device.id),
            'device_name': device.name,
            'status_level': status_level,
            'reasons': reasons,
            'battery_level': battery_level,
            'is_charging': is_charging,
            'network_available': network_available,
            'unsent_notifications': unsent_notifications,
            'last_notification_timestamp': last_notification_timestamp.isoformat() if last_notification_timestamp else None,
            'timestamp': timestamp,
            'app_version': app_version,
            'android_version': android_version,
            'device_model': device_model,
            'battery_report_id': str(battery_report.id),
            'status_report_id': str(device_status.id)
        }, status=status.HTTP_200_OK)


class MessageView(APIView):
    """
    Отправка экстренного сообщения
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="🚨 Отправить экстренное сообщение",
        operation_description="""
        Создает новое экстренное сообщение от устройства.
        
        **Аутентификация**: Требуется заголовок `X-TOKEN` с токеном устройства.
        
        **Использование**:
        - Отправка экстренных сообщений в случае опасности
        - Уведомление администратора о проблемах
        - Передача важной информации от устройства
        
        **Автоматические действия**:
        - Отправка уведомления в Telegram администратору
        - Обновление `last_seen` устройства на текущее время
        - Сохранение сообщения в базе данных
        
        **Формат уведомления в Telegram**:
        ```
        🚨 НОВОЕ СООБЩЕНИЕ
        
        📱 Устройство: [Название устройства]
        ⏰ Время: [Дата и время]
        👤 Отправитель: [Имя отправителя]
        
        💬 Сообщение:
        [Текст сообщения]
        ```
        """,
        tags=['Экстренные сообщения'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['sender', 'text'],
            properties={
                'sender': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Имя отправителя сообщения',
                    max_length=100,
                    example='Иван Петров'
                ),
                'text': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Текст экстренного сообщения',
                    max_length=1000,
                    example='Помогите! Застрял в лифте на 5 этаже!'
                ),
                'package_name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Имя пакета приложения, отправившего уведомление (например: com.onlyone.app.FC)',
                    example='com.onlyone.app.FC'
                ),
                'date_created': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_DATETIME,
                    description='Дата и время создания сообщения (ISO 8601). Если не указано, используется текущее время',
                    example='2024-01-15T14:30:25Z'
                )
            }
        ),
        responses={
            201: openapi.Response(
                description="Сообщение успешно отправлено или отфильтровано",
                examples={
                    "application/json": {
                        "id": "550e8400-e29b-41d4-a716-446655440002",
                        "message": "Сообщение успешно отправлено",
                        "filtered": False,
                        "filter_reason": None
                    }
                }
            ),
            400: openapi.Response(
                description="Ошибка валидации данных",
                examples={
                    "application/json": {
                        "sender": ["Это поле обязательно."],
                        "text": ["Это поле обязательно."]
                    }
                }
            ),
            401: openapi.Response(
                description="Неверный или отсутствующий токен аутентификации",
                examples={
                    "application/json": {
                        "detail": "Authentication credentials were not provided."
                    }
                }
            ),
            500: openapi.Response(
                description="Ошибка отправки уведомления в Telegram",
                examples={
                    "application/json": {
                        "error": "Failed to send notification to Telegram"
                    }
                }
            )
        },
        manual_parameters=[
            openapi.Parameter(
                'X-TOKEN',
                openapi.IN_HEADER,
                description="Токен аутентификации устройства",
                type=openapi.TYPE_STRING,
                required=True,
                example="abc123def456ghi789"
            )
        ]
    )
    def post(self, request):
        device = request.user
        serializer = MessageSerializer(data=request.data)
        
        if serializer.is_valid():
            # Получаем данные для фильтрации
            package_name = request.data.get('package_name', '')
            sender = request.data.get('sender', '')
            text = request.data.get('text', '')
            
            # Проверяем, нужно ли фильтровать уведомление
            should_filter, filter_reason = NotificationFilterService.should_filter_notification(
                package_name=package_name,
                sender=sender,
                text=text
            )
            
            # Если сообщение должно быть отфильтровано - не сохраняем в БД и не отправляем уведомление
            if should_filter:
                # Update device last_seen
                device.last_seen = timezone.now()
                device.save(update_fields=['last_seen'])
                
                return Response(
                    {
                        'message': f'Сообщение отфильтровано: {filter_reason}',
                        'filtered': True,
                        'filter_reason': filter_reason
                    }, 
                    status=status.HTTP_200_OK
                )
            
            # Создаем сообщение только если оно не отфильтровано
            message = serializer.save(
                device=device,
                raw_payload=request.data,
                is_filtered=False,
                filter_reason=""
            )
            
            # Update device last_seen
            device.last_seen = timezone.now()
            device.save(update_fields=['last_seen'])
            
            # Send notification to admin chat ТОЛЬКО для неотфильтрованных сообщений
            notification_text = f"🚨 <b>НОВОЕ СООБЩЕНИЕ</b>\n\n"
            notification_text += f"{device.name} {message.date_created.strftime('%d.%m.%Y %H:%M:%S')}\n\n"
            notification_text += f"💬 <b>Сообщение:</b>\n{message.text}"
            
            # TODO: Move to Celery for async processing
            notify(notification_text)
            
            return Response(
                {
                    'id': str(message.id), 
                    'message': 'Сообщение успешно отправлено',
                    'filtered': False,
                    'filter_reason': None
                }, 
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogFileView(APIView):
    """
    Загрузка txt файла с логом
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="📄 Загрузить лог файл",
        operation_description="""
        Загружает txt файл с логом от устройства.
        
        **Аутентификация**: Требуется заголовок `X-TOKEN` с токеном устройства.
        
        **Использование**:
        - Загрузка логов от мобильного устройства
        - Сохранение текстовых файлов с информацией о работе устройства
        - Архивирование важной информации от устройства
        
        **Автоматические действия**:
        - Обновление `last_seen` устройства на текущее время
        - Сохранение содержимого файла в базе данных
        - Парсинг txt файла и извлечение текста
        """,
        tags=['Лог файлы'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['file'],
            properties={
                'file': openapi.Schema(
                    type=openapi.TYPE_FILE,
                    description='TXT файл с логом для загрузки',
                    format=openapi.FORMAT_BINARY
                ),
                'date_created': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_DATETIME,
                    description='Дата и время создания лога (ISO 8601). Если не указано, используется текущее время',
                    example='2024-01-15T14:30:25Z'
                )
            }
        ),
        responses={
            201: openapi.Response(
                description="Лог файл успешно загружен",
                examples={
                    "application/json": {
                        "id": "550e8400-e29b-41d4-a716-446655440003",
                        "message": "Лог файл успешно загружен",
                        "file_size": 1024
                    }
                }
            ),
            400: openapi.Response(
                description="Ошибка валидации данных",
                examples={
                    "application/json": {
                        "file": ["Это поле обязательно."],
                        "error": "Недопустимый формат файла. Разрешены только .txt файлы."
                    }
                }
            ),
            401: openapi.Response(
                description="Неверный или отсутствующий токен аутентификации",
                examples={
                    "application/json": {
                        "detail": "Authentication credentials were not provided."
                    }
                }
            )
        },
        manual_parameters=[
            openapi.Parameter(
                'X-TOKEN',
                openapi.IN_HEADER,
                description="Токен аутентификации устройства",
                type=openapi.TYPE_STRING,
                required=True,
                example="abc123def456ghi789"
            )
        ]
    )
    def post(self, request):
        device = request.user
        
        # Проверяем наличие файла
        if 'file' not in request.FILES:
            return Response(
                {'file': ['Это поле обязательно.']}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        uploaded_file = request.FILES['file']
        
        # Проверяем расширение файла
        if not uploaded_file.name.lower().endswith('.txt'):
            return Response(
                {'error': 'Недопустимый формат файла. Разрешены только .txt файлы.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверяем размер файла (максимум 50 MB)
        max_size = 50 * 1024 * 1024  # 50 MB
        if uploaded_file.size > max_size:
            return Response(
                {'error': f'Файл слишком большой. Максимальный размер: {max_size // 1024 // 1024} MB'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Подготавливаем данные для сериализатора
        data = {
            'file': uploaded_file,
            'date_created': request.data.get('date_created')
        }
        
        serializer = LogFileSerializer(data=data)
        
        if serializer.is_valid():
            # Читаем содержимое файла для превью
            try:
                file_content = uploaded_file.read().decode('utf-8')
                # Возвращаем указатель файла в начало
                uploaded_file.seek(0)
            except UnicodeDecodeError:
                return Response(
                    {'error': 'Ошибка чтения файла. Убедитесь, что файл содержит текст в кодировке UTF-8.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Создаем запись лога с файлом и превью текста
            log_file = serializer.save(
                device=device,
                text=file_content[:1000] + "..." if len(file_content) > 1000 else file_content
            )
            
            # Update device last_seen
            device.last_seen = timezone.now()
            device.save(update_fields=['last_seen'])
            
            # Send notification to admin chat with file
            notification_text = f"📄 <b>НОВЫЙ ЛОГ ФАЙЛ</b>\n\n"
            notification_text += f"📱 Устройство: {device.name}\n"
            notification_text += f"⏰ Время: {log_file.date_created.strftime('%d.%m.%Y %H:%M:%S')}\n"
            notification_text += f"📊 Размер: {len(file_content)} символов\n"
            notification_text += f"📁 Файл: {uploaded_file.name}\n"
            notification_text += f"🔗 Скачать: <a href='{log_file.file.url}'>Открыть файл</a>"
            
            # TODO: Move to Celery for async processing
            notify(notification_text)
            
            return Response(
                {
                    'id': str(log_file.id), 
                    'message': 'Лог файл успешно загружен',
                    'file_size': len(file_content),
                    'file_name': uploaded_file.name
                }, 
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
