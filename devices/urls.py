from django.urls import path
from . import views

urlpatterns = [
    path('device', views.DeviceView.as_view(), name='device'),
    path('mobile/battery', views.BatteryReportView.as_view(), name='battery'),
    path('mobile/message', views.MessageView.as_view(), name='message'),
]

