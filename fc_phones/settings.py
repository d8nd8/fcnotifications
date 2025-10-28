"""
Django settings for fc_phones project.
"""

from pathlib import Path
from decouple import config
import os
from django.urls import reverse_lazy, reverse
from django.templatetags.static import static

# Build paths inside the project like this: BASE_DIR / 'subdir'.

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: [s.strip() for s in v.split(',')])

# Application definition
INSTALLED_APPS = [
    'unfold',  # Unfold должен быть перед django.contrib.admin
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'drf_yasg',
    'devices',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'fc_phones.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'fc_phones.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

# Форматы даты и времени для русского языка
DATE_FORMAT = 'd.m.Y'
DATETIME_FORMAT = 'd.m.Y H:i'
TIME_FORMAT = 'H:i'
SHORT_DATE_FORMAT = 'd.m.Y'
SHORT_DATETIME_FORMAT = 'd.m.Y H:i'

# Первый день недели (0 = воскресенье, 1 = понедельник)
FIRST_DAY_OF_WEEK = 1

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'devices.authentication.XTokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# Telegram Bot settings
TELEGRAM_BOT_TOKEN = config('TELEGRAM_BOT_TOKEN', default='')
TELEGRAM_ADMIN_CHAT_ID = config('TELEGRAM_ADMIN_CHAT_ID', default='')

# File upload settings
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50 MB


UNFOLD = {
    "SITE_URL": "/",
    "SITE_SYMBOL": "📱",
    "SITE_HEADER": "FC Phones",
    "BORDER_RADIUS": "10px",
    "DASHBOARD_CALLBACK": "devices.admin.dashboard_callback",
    "SHOW_HISTORY": False,
    "SHOW_VIEW_ON_SITE": False,
    "STYLES": [
        lambda request: static("css/custom.css"),
    ],
    "SCRIPTS": [
        lambda request: static("js/custom.js"),
    ],
    "COLORS": {
        "primary": {
            "50": "250 245 255",
            "100": "243 232 255",
            "200": "233 213 255",
            "300": "216 180 254",
            "400": "196 181 253",
            "500": "168 85 247",
            "600": "147 51 234",
            "700": "126 34 206",
            "800": "107 33 168",
            "900": "88 28 135",
            "950": "59 7 100",
        },
    },
    "SIDEBAR": {
        "show_search": False,
        "show_all_applications": False,
        "navigation": [
            {
                "items": [
                    {
                        "title": "Сводка",
                        "icon": "dashboard",
                        "link": "/admin/",
                    },
                ],
            },
            {
                "items": [
                    {
                        "title": "Статус устройств",
                        "icon": "analytics",
                        "link": "/admin/devices/devicestatus/",
                    },
                    {
                        "title": "Сообщения",
                        "icon": "message",
                        "link": "/admin/devices/message/",
                    },
                    {
                        "title": "Лог файлы",
                        "icon": "description",
                        "link": "/admin/devices/logfile/",
                    },
                    {
                        "title": "Фильтры уведомлений",
                        "icon": "filter_list",
                        "link": "/admin/devices/notificationfilter/",
                    },
                    {
                        "title": "Токены устройств",
                        "icon": "phone",
                        "link": "/admin/devices/device/",
                    },
                    {
                        "title": "Пользователи Telegram",
                        "icon": "people",
                        "link": "/admin/devices/telegramuser/",
                    },
                    {
                        "title": "Токены авторизации",
                        "icon": "key",
                        "link": "/admin/devices/authtoken/",
                    },
                ],
            },
            {
                "items": [
                    {
                        "title": "Swagger",
                        "icon": "api",
                        "link": "/api/docs/",
                    },
                ],
            },
        ],
    },
}

