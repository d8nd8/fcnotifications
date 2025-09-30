from rest_framework import serializers
from .models import Device, BatteryReport, Message
from django.utils import timezone


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ['id', 'external_id', 'token', 'name', 'last_seen', 'created_at']


class BatteryReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = BatteryReport
        fields = ['battery_level', 'date_created']
    
    def validate_battery_level(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("Уровень батареи должен быть от 0 до 100")
        return value
    
    def validate_date_created(self, value):
        if value and value > timezone.now():
            raise serializers.ValidationError("Дата создания не может быть в будущем")
        return value


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['date_created', 'sender', 'text']
    
    def validate_date_created(self, value):
        if value and value > timezone.now():
            raise serializers.ValidationError("Дата создания не может быть в будущем")
        return value
