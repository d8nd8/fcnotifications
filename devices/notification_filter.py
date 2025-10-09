"""
Сервис для фильтрации уведомлений
"""
from .models import NotificationFilter
import re
from typing import Tuple, Optional


class NotificationFilterService:
    """
    Сервис для фильтрации уведомлений по пакетам приложений
    """
    
    # Системные пакеты Android, которые обычно нужно фильтровать
    SYSTEM_PACKAGES = [
        'com.android.systemui',
        'com.android.providers.downloads',
        'com.oppo.ota',
        'com.google.android.deskclock',
        'com.android.settings',
        'com.android.providers.media',
        'com.google.android.gms',
        'com.google.android.apps.messaging',
        'com.android.phone',
        'com.android.calendar',
        'com.android.providers.calendar',
        'com.android.providers.contacts',
        'com.android.providers.telephony',
        'com.android.providers.settings',
        'com.android.providers.userdictionary',
        'com.android.providers.downloads.ui',
        'com.android.providers.media.documents',
        'com.android.documentsui',
        'com.android.packageinstaller',
        'com.android.shell',
        'com.android.systemui.recents',
        'com.android.systemui.statusbar',
        'com.android.systemui.notification',
        'com.onlyone.app.FC',  # Ваш пример
    ]
    
    @classmethod
    def should_filter_notification(cls, package_name: str, sender: str = None, text: str = None) -> Tuple[bool, str]:
        """
        Проверяет, нужно ли фильтровать уведомление
        
        Args:
            package_name: Имя пакета приложения
            sender: Отправитель уведомления
            text: Текст уведомления
            
        Returns:
            Tuple[bool, str]: (нужно_ли_фильтровать, причина_фильтрации)
        """
        if not package_name:
            return False, ""
        
        # ХАРДКОД - фильтруем ВСЕ сообщения кроме банковских SMS
        # Разрешаем только SMS от банков и операторов
        
        # Сначала проверяем системные паттерны - если найдены, то ВСЕГДА фильтруем
        if text and cls._is_system_message(text):
            return True, "Системное сообщение - фильтруется"
        
        # Только для SMS проверяем банковские паттерны
        if package_name == 'com.google.android.apps.messaging':
            # Проверяем, является ли это банковским SMS
            if text and cls._is_banking_sms(text):
                return False, ""  # НЕ фильтруем банковские SMS
            else:
                return True, "Фильтр: только банковские SMS разрешены"
        
        # Фильтруем ВСЕ остальные сообщения
        return True, "Фильтр: только банковские SMS разрешены"
    
    @classmethod
    def _is_system_message(cls, text: str) -> bool:
        """
        Проверяет, является ли сообщение системным (нужно фильтровать)
        """
        if not text:
            return True  # Пустые сообщения фильтруем
        
        # Системные паттерны для фильтрации
        system_patterns = [
            r'^No Content$',
            r'Осталось совсем немного',
            r'Чтобы продолжить, подключитесь к Интернету',
            r'Безопасная загрузка проверенных приложений',
            r'This service is running in the foreground',
            r'Download completed',
            r'Download failed',
            r'System update',
            r'OTA update',
            r'Battery optimization',
            r'Storage space',
            r'Background app',
            r'App installed',
            r'App updated',
            r'Осталось:\s*\d+\s*%',
            r'Выполняем проверку контента',
            r'Нажмите, чтобы настроить',
            r'Ваш телефон был автоматически отсоединен',
        ]
        
        for pattern in system_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    @classmethod
    def _is_banking_sms(cls, text: str) -> bool:
        """
        Проверяет, является ли SMS банковским (важным)
        """
        if not text:
            return False
        
        # Паттерны банковских SMS
        banking_patterns = [
            r'Снятие наличных',
            r'Баланс:',
            r'Код:\s*\d+',
            r'код\s*\d+',
            r'Пожалуйста, получив сообщение',
            r'Уважаемый Клиент',
            r'С заботой о Вас',
            r'voshel v.*Onlajn',
            r'Polzovatel.*voshel',
            r'RMX\d+',
            r'Обновление системы',
            r'Критическое обновление',
            r'Вам было отправлено СМС',
            r'Пытались с вами связаться',
            r'Никому не сообщайте код',
            r'код подтверждения',
            r'вход в.*код',
            r'СберБизнес',
            r'ВТБ',
            r'Альфа.*код',
            r'LOCKO.*код',
            r'BLANC.*код',
            r'Тинькофф',
            r'Райффайзен',
            r'Газпромбанк',
            r'Альфа-Банк',
            r'Сбербанк',
            r'VTB',
            r'Тинькофф Банк',
            r'Райффайзенбанк',
            r'Газпромбанк',
            r'МТС Банк',
            r'Росбанк',
            r'УралСиб',
            r'Хоум Кредит',
            r'Ренессанс Кредит',
            r'ОТП Банк',
            r'ЮниКредит Банк',
            r'Россельхозбанк',
            r'Почта Банк',
            r'МКБ',
            r'Ак Барс',
            r'Совкомбанк',
            r'Точка',
            r'Модульбанк',
            r'Альфа-Банк',
            r'Банк Открытие',
            r'Промсвязьбанк',
            r'Росбанк',
            r'Сбербанк',
            r'ВТБ',
            r'Тинькофф',
            r'Альфа',
            r'LOCKO',
            r'BLANC',
            r'МТС',
            r'Билайн',
            r'МегаФон',
            r'Теле2',
            r'Yota',
            r'Ростелеком',
            r'МТС',
            r'Билайн',
            r'МегаФон',
            r'Теле2',
            r'Yota',
            r'Ростелеком',
        ]
        
        
        for pattern in banking_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    
    @classmethod
    def create_default_filters(cls):
        """Создает фильтры по умолчанию"""
        default_filters = [
            {
                'package_name': 'com.onlyone.app.FC',
                'description': 'Системное приложение FC',
                'filter_type': 'blacklist'
            },
            {
                'package_name': 'com.android.providers.downloads',
                'description': 'Менеджер загрузок Android',
                'filter_type': 'blacklist'
            },
            {
                'package_name': 'com.oppo.ota',
                'description': 'Система обновлений OPPO',
                'filter_type': 'blacklist'
            },
            {
                'package_name': 'com.google.android.deskclock',
                'description': 'Будильник Google',
                'filter_type': 'blacklist'
            },
            {
                'package_name': 'com.android.systemui',
                'description': 'Системный интерфейс Android',
                'filter_type': 'blacklist'
            },
            {
                'package_name': 'com.android.*',
                'description': 'Все системные пакеты Android',
                'filter_type': 'blacklist'
            },
            {
                'package_name': 'com.google.android.*',
                'description': 'Все системные пакеты Google',
                'filter_type': 'blacklist'
            }
        ]
        
        for filter_data in default_filters:
            NotificationFilter.objects.get_or_create(
                package_name=filter_data['package_name'],
                defaults={
                    'description': filter_data['description'],
                    'filter_type': filter_data['filter_type'],
                    'is_active': True
                }
            )
