from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Device, BatteryReport, Message
from .serializers import DeviceSerializer, BatteryReportSerializer, MessageSerializer
from .notifications import notify


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
                description="Сообщение успешно отправлено",
                examples={
                    "application/json": {
                        "id": "550e8400-e29b-41d4-a716-446655440002",
                        "message": "Сообщение успешно отправлено"
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
            # Create message with raw_payload
            message = serializer.save(
                device=device,
                raw_payload=request.data
            )
            
            # Update device last_seen
            device.last_seen = timezone.now()
            device.save(update_fields=['last_seen'])
            
            # Send notification to admin chat
            notification_text = f"🚨 <b>НОВОЕ СООБЩЕНИЕ</b>\n\n"
            notification_text += f"📱 <b>Устройство:</b> {device.name}\n"
            notification_text += f"⏰ <b>Время:</b> {message.date_created.strftime('%d.%m.%Y %H:%M:%S')}\n"
            notification_text += f"👤 <b>Отправитель:</b> {message.sender}\n\n"
            notification_text += f"💬 <b>Сообщение:</b>\n{message.text}"
            
            # TODO: Move to Celery for async processing
            notify(notification_text)
            
            return Response(
                {'id': str(message.id), 'message': 'Сообщение успешно отправлено'}, 
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
