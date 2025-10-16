from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Device, BatteryReport, Message, LogFile
from .serializers import DeviceSerializer, BatteryReportSerializer, MessageSerializer, LogFileSerializer
from .notifications import notify
from .notification_filter import NotificationFilterService


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


class BatteryReportView(APIView):
    """
    Отправка отчета о состоянии батареи
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="🔋 Отправить отчет о батарее",
        operation_description="""
        Создает новый отчет о состоянии батареи устройства.
        
        **Аутентификация**: Требуется заголовок `X-TOKEN` с токеном устройства.
        
        **Использование**:
        - Отправка keep-alive сигналов от устройства
        - Мониторинг уровня заряда батареи
        - Обновление времени последней активности устройства
        
        **Автоматические действия**:
        - Обновление `last_seen` устройства на текущее время
        - Сохранение отчета в базе данных
        """,
        tags=['Мониторинг батареи'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['battery_level'],
            properties={
                'battery_level': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='Уровень заряда батареи в процентах (0-100)',
                    minimum=0,
                    maximum=100,
                    example=85
                ),
                'date_created': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_DATETIME,
                    description='Дата и время создания отчета (ISO 8601). Если не указано, используется текущее время',
                    example='2024-01-15T14:30:25Z'
                )
            }
        ),
        responses={
            201: openapi.Response(
                description="Отчет о батарее успешно создан",
                examples={
                    "application/json": {
                        "id": "550e8400-e29b-41d4-a716-446655440001",
                        "message": "Отчет о батарее успешно создан"
                    }
                }
            ),
            400: openapi.Response(
                description="Ошибка валидации данных",
                examples={
                    "application/json": {
                        "battery_level": ["Уровень батареи должен быть от 0 до 100"]
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
        serializer = BatteryReportSerializer(data=request.data)
        
        if serializer.is_valid():
            # Create battery report
            battery_report = serializer.save(device=device)
            
            # Update device last_seen
            device.last_seen = timezone.now()
            device.save(update_fields=['last_seen'])
            
            return Response(
                {'id': str(battery_report.id), 'message': 'Отчет о батарее успешно создан'}, 
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
        
        # Читаем содержимое файла
        try:
            file_content = uploaded_file.read().decode('utf-8')
        except UnicodeDecodeError:
            return Response(
                {'error': 'Ошибка чтения файла. Убедитесь, что файл содержит текст в кодировке UTF-8.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Подготавливаем данные для сериализатора
        data = {
            'text': file_content,
            'date_created': request.data.get('date_created')
        }
        
        serializer = LogFileSerializer(data=data)
        
        if serializer.is_valid():
            # Создаем запись лога
            log_file = serializer.save(device=device)
            
            # Update device last_seen
            device.last_seen = timezone.now()
            device.save(update_fields=['last_seen'])
            
            # Send notification to admin chat
            notification_text = f"📄 <b>НОВЫЙ ЛОГ ФАЙЛ</b>\n\n"
            notification_text += f"📱 Устройство: {device.name}\n"
            notification_text += f"⏰ Время: {log_file.date_created.strftime('%d.%m.%Y %H:%M:%S')}\n"
            notification_text += f"📊 Размер: {len(file_content)} символов\n\n"
            notification_text += f"📝 <b>Содержимое лога:</b>\n"
            
            # Обрезаем текст лога для уведомления (первые 500 символов)
            log_preview = file_content[:500]
            if len(file_content) > 500:
                log_preview += "\n... (полный лог доступен в админке)"
            
            notification_text += f"<pre>{log_preview}</pre>"
            
            # TODO: Move to Celery for async processing
            notify(notification_text)
            
            return Response(
                {
                    'id': str(log_file.id), 
                    'message': 'Лог файл успешно загружен',
                    'file_size': len(file_content)
                }, 
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
