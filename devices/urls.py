from django.urls import path
from . import views

urlpatterns = [
    path('device', views.DeviceView.as_view(), name='device'),
    path('battery-report', views.SimpleBatteryReportView.as_view(), name='simple-battery'),
    path('mobile/message', views.MessageView.as_view(), name='message'),
    path('mobile/log', views.LogFileView.as_view(), name='log'),
]

