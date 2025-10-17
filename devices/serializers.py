from rest_framework import serializers
from .models import Device, BatteryReport, Message, LogFile
from django.utils import timezone
from datetime import timedelta
from drf_yasg import openapi


class DeviceSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Device
    """
    id = serializers.UUIDField(read_only=True, help_text="Уникальный идентификатор устройства")
    token = serializers.CharField(read_only=True, help_text="Токен аутентификации устройства")
    name = serializers.CharField(read_only=True, help_text="Название устройства")
    last_seen = serializers.DateTimeField(read_only=True, help_text="Время последней активности")
    created_at = serializers.DateTimeField(read_only=True, help_text="Дата создания устройства")
    
    class Meta:
        model = Device
        fields = ['id', 'token', 'name', 'last_seen', 'created_at']


class BatteryReportSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели BatteryReport
    """
    battery_level = serializers.IntegerField(
        min_value=0, 
        max_value=100,
        help_text="Уровень заряда батареи в процентах (0-100)"
    )
    date_created = serializers.DateTimeField(
        required=False,
        help_text="Дата и время создания отчета (ISO 8601). Если не указано, используется текущее время"
    )
    
    class Meta:
        model = BatteryReport
        fields = ['battery_level', 'date_created']
    
    def validate_battery_level(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("Уровень батареи должен быть от 0 до 100")
        return value
    
    def validate_date_created(self, value):
        if value:
            # Добавляем буфер в 1 час для учета разницы часовых поясов
            now_plus_buffer = timezone.now() + timedelta(hours=1)
            if value > now_plus_buffer:
                raise serializers.ValidationError("Дата создания не может быть в будущем")
        return value


class MessageSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Message
    """
    sender = serializers.CharField(
        max_length=100,
        help_text="Имя отправителя сообщения"
    )
    text = serializers.CharField(
        max_length=1000,
        help_text="Текст экстренного сообщения"
    )
    package_name = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Имя пакета приложения, отправившего уведомление"
    )
    date_created = serializers.DateTimeField(
        required=False,
        help_text="Дата и время создания сообщения (ISO 8601). Если не указано, используется текущее время"
    )
    
    class Meta:
        model = Message
        fields = ['date_created', 'sender', 'text', 'package_name']
    
    def validate_date_created(self, value):
        if value:
            # Добавляем буфер в 1 час для учета разницы часовых поясов
            now_plus_buffer = timezone.now() + timedelta(hours=1)
            if value > now_plus_buffer:
                raise serializers.ValidationError("Дата создания не может быть в будущем")
        return value


class LogFileSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели LogFile
    """
    file = serializers.FileField(
        help_text="Файл лога для загрузки"
    )
    text = serializers.CharField(
        required=False,
        help_text="Превью текста лога (генерируется автоматически)"
    )
    date_created = serializers.DateTimeField(
        required=False,
        help_text="Дата и время создания лога (ISO 8601). Если не указано, используется текущее время"
    )
    
    class Meta:
        model = LogFile
        fields = ['file', 'text', 'date_created']
    
    def validate_date_created(self, value):
        if value:
            # Добавляем буфер в 1 час для учета разницы часовых поясов
            now_plus_buffer = timezone.now() + timedelta(hours=1)
            if value > now_plus_buffer:
                raise serializers.ValidationError("Дата создания не может быть в будущем")
        return value
