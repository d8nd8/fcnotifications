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
        
        # Специальная логика для SMS - разрешаем только важные
        if package_name == 'com.google.android.apps.messaging':
            return cls._check_sms_importance(text)
        
        # Проверяем правила из базы данных
        db_result = cls._check_database_filters(package_name)
        if db_result[0]:
            return db_result
        
        # Проверяем системные пакеты
        if cls._is_system_package(package_name):
            return True, f"Системный пакет: {package_name}"
        
        # Проверяем по паттернам
        pattern_result = cls._check_pattern_filters(package_name, sender, text)
        if pattern_result[0]:
            return pattern_result
        
        return False, ""
    
    @classmethod
    def _check_sms_importance(cls, text: str) -> Tuple[bool, str]:
        """
        Проверяет важность SMS сообщения
        Разрешаем только важные SMS от банков и операторов
        """
        if not text:
            return True, "Пустое SMS сообщение"
        
        # Паттерны важных SMS (НЕ фильтруем)
        important_patterns = [
            r'Снятие наличных',  # Банковские операции
            r'Баланс:',  # Информация о балансе
            r'Код:\s*\d+',  # SMS коды
            r'код\s*\d+',  # SMS коды (строчными буквами)
            r'Пожалуйста, получив сообщение',  # Настройки оператора
            r'Уважаемый Клиент',  # Официальные уведомления
            r'С заботой о Вас',  # Официальные уведомления
            r'voshel v.*Onlajn',  # Банковские уведомления
            r'Polzovatel.*voshel',  # Банковские уведомления
            r'RMX\d+',  # OTA обновления (важные)
            r'Обновление системы',  # Системные обновления
            r'Критическое обновление',  # Критические обновления
            r'Вам было отправлено СМС',  # Настройки интернета
            r'Пытались с вами связаться',  # Важные уведомления
            r'Никому не сообщайте код',  # Банковские коды
            r'код подтверждения',  # Коды подтверждения
            r'вход в.*код',  # Коды входа
            r'СберБизнес',  # Сбербанк бизнес
            r'ВТБ',  # ВТБ банк
            r'Альфа.*код',  # Альфа-банк коды
            r'LOCKO.*код',  # Локо-банк коды
            r'BLANC.*код',  # Бланк банк коды
        ]
        
        # Проверяем, является ли SMS важным
        for pattern in important_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False, ""  # НЕ фильтруем важные SMS
        
        # Если не найдено важных паттернов - фильтруем
        return True, "Неважное SMS сообщение"
    
    @classmethod
    def _check_database_filters(cls, package_name: str) -> Tuple[bool, str]:
        """Проверяет фильтры из базы данных"""
        try:
            # Ищем точное совпадение
            exact_filter = NotificationFilter.objects.filter(
                package_name=package_name,
                is_active=True
            ).first()
            
            if exact_filter:
                if exact_filter.filter_type == 'blacklist':
                    return True, f"В черном списке: {package_name}"
                elif exact_filter.filter_type == 'whitelist':
                    return False, ""
            
            # Ищем по паттернам (wildcard)
            wildcard_filters = NotificationFilter.objects.filter(
                package_name__contains='*',
                is_active=True
            )
            
            for filter_rule in wildcard_filters:
                pattern = filter_rule.package_name.replace('*', '.*')
                if re.match(pattern, package_name):
                    if filter_rule.filter_type == 'blacklist':
                        return True, f"Паттерн в черном списке: {filter_rule.package_name}"
                    elif filter_rule.filter_type == 'whitelist':
                        return False, ""
                        
        except Exception as e:
            # Если ошибка с БД, продолжаем с другими проверками
            pass
        
        return False, ""
    
    @classmethod
    def _is_system_package(cls, package_name: str) -> bool:
        """Проверяет, является ли пакет системным"""
        return package_name in cls.SYSTEM_PACKAGES
    
    @classmethod
    def _check_pattern_filters(cls, package_name: str, sender: str = None, text: str = None) -> Tuple[bool, str]:
        """Проверяет фильтры по паттернам"""
        
        # Фильтры по паттернам пакетов
        package_patterns = [
            r'^com\.android\.',  # Все Android системные пакеты
            r'^com\.google\.android\.',  # Google системные пакеты
            r'^com\.oppo\.',  # OPPO системные пакеты
            r'^com\.samsung\.',  # Samsung системные пакеты
            r'^com\.xiaomi\.',  # Xiaomi системные пакеты
            r'^com\.huawei\.',  # Huawei системные пакеты
            r'^com\.oneplus\.',  # OnePlus системные пакеты
            r'^com\.onlyone\.app\.FC',  # Ваш конкретный пример
        ]
        
        for pattern in package_patterns:
            if re.match(pattern, package_name):
                return True, f"Системный паттерн: {pattern}"
        
        # Фильтры по отправителю
        if sender:
            sender_patterns = [
                r'^System$',
                r'^Android System$',
                r'^Settings$',
                r'^Download Manager$',
                r'^Media Storage$',
                r'^Package Installer$',
            ]
            
            for pattern in sender_patterns:
                if re.match(pattern, sender, re.IGNORECASE):
                    return True, f"Системный отправитель: {sender}"
        
        # Фильтры по тексту
        if text:
            text_patterns = [
                r'Download completed',
                r'Download failed',
                r'System update',
                r'OTA update',
                r'Battery optimization',
                r'Storage space',
                r'Background app',
                r'App installed',
                r'App updated',
                r'This service is running in the foreground',  # Ваше приложение
                r'Осталось:\s*\d+\s*%',  # Процент батареи
                r'Выполняем проверку контента',  # Системные уведомления
                r'Нажмите, чтобы настроить',  # Системные уведомления
                r'Ваш телефон был автоматически отсоединен',  # Системные уведомления
                r'No Content',  # Пустые уведомления
                r'Снятие наличных',  # Банковские SMS
                r'Баланс:',  # Банковские SMS
                r'Код:\s*\d+',  # SMS коды
                r'Пожалуйста, получив сообщение',  # Настройки оператора
                r'Уважаемый Клиент',  # Рекламные SMS
                r'С заботой о Вас',  # Рекламные SMS
                r'voshel v.*Onlajn',  # Банковские уведомления
            ]
            
            for pattern in text_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return True, f"Системный текст: {pattern}"
        
        return False, ""
    
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
