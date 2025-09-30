from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Device, BatteryReport, Message
from .serializers import DeviceSerializer, BatteryReportSerializer, MessageSerializer
from .notifications import notify


class DeviceView(APIView):
    """
    GET /device - Returns device information for authenticated device
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        device = request.user  # This will be the Device instance from XTokenAuthentication
        serializer = DeviceSerializer(device)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BatteryReportView(APIView):
    """
    POST /mobile/battery - Creates a new battery report
    """
    permission_classes = [IsAuthenticated]
    
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
    POST /mobile/message - Creates a new message
    """
    permission_classes = [IsAuthenticated]
    
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
