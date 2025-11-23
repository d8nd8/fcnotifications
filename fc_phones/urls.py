"""
URL configuration for fc_phones project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="FC Phones API",
        default_version='v1',
        description="""
        # 📱 FC Phones API - Сервис Алертов для Мобильных Устройств
        
        ## Описание
        API для системы мониторинга мобильных устройств с уведомлениями в Telegram.
        Позволяет устройствам отправлять сообщения о состоянии батареи и экстренные сообщения.
        
        ## Аутентификация
        Все API endpoints требуют аутентификации через заголовок `X-TOKEN` с токеном устройства.
        
        ## Основные возможности
        - 📊 **Мониторинг батареи** - отслеживание уровня заряда устройств
        - 🚨 **Экстренные сообщения** - отправка уведомлений в Telegram
        - 📱 **Управление устройствами** - регистрация и мониторинг устройств
        - 🔔 **Telegram интеграция** - автоматические уведомления администратору
        
        ## Поддерживаемые форматы
        - **Content-Type**: `application/json`
        - **Ответы**: JSON
        
        ## Коды ответов
        - `200` - Успешный запрос
        - `201` - Ресурс создан
        - `400` - Ошибка валидации
        - `401` - Неверный токен аутентификации
        - `500` - Внутренняя ошибка сервера
        """,
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('', RedirectView.as_view(url='/admin/', permanent=False), name='index'),  # Редирект на админ-панель
    path('admin/', admin.site.urls),
    path('api/', include('devices.urls')),
    re_path(r'^api/docs(?P<format>\.(json|yaml))$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Добавляем URL для медиа файлов в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

