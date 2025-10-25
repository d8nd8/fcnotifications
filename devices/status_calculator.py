"""
Утилиты для расчета статуса устройства
"""
from django.utils import timezone
from datetime import timedelta


class DeviceStatusCalculator:
    """
    Класс для расчета статуса устройства и причин
    """
    
    @staticmethod
    def calculate_status_level(battery_level, is_charging, network_available, 
                             unsent_notifications, last_notification_timestamp):
        """
        Рассчитывает общий статус устройства на основе различных параметров
        
        Args:
            battery_level (int): Уровень батареи (0-100)
            is_charging (bool): Заряжается ли устройство
            network_available (bool): Есть ли доступ к интернету
            unsent_notifications (int): Количество неотправленных уведомлений
            last_notification_timestamp (datetime): Время последнего уведомления
            
        Returns:
            tuple: (status_level, reasons)
        """
        reasons = []
        status_level = "SUCCESS"
        
        # Проверка критических ошибок (ERROR)
        if battery_level <= 5:
            reasons.append("Батарея ≤ 5% (телефон может выключиться)")
            status_level = "ERROR"
        elif not network_available:
            reasons.append("Нет интернета")
            status_level = "ERROR"
        elif unsent_notifications > 10:
            reasons.append(f"Количество неотправленных уведомлений > 10 ({unsent_notifications})")
            status_level = "ERROR"
        elif last_notification_timestamp:
            # Проверяем, если последнее уведомление было более 3 часов назад
            time_since_last_notification = timezone.now() - last_notification_timestamp
            if time_since_last_notification > timedelta(hours=3):
                reasons.append("Нет входящих уведомлений более 3 часов")
                status_level = "ERROR"
        
        # Если уже ERROR, не проверяем ATTENTION
        if status_level == "ERROR":
            return status_level, reasons
        
        # Проверка предупреждений (ATTENTION)
        if battery_level <= 10 and not is_charging:
            reasons.append("Заряд батареи 10% или меньше")
            status_level = "ATTENTION"
        
        if unsent_notifications > 0:
            reasons.append(f"Есть неотправленные уведомления ({unsent_notifications})")
            status_level = "ATTENTION"
        
        if last_notification_timestamp:
            # Проверяем, если последнее уведомление было более 1 часа назад
            time_since_last_notification = timezone.now() - last_notification_timestamp
            if time_since_last_notification > timedelta(hours=1):
                reasons.append("В течение последнего часа не приходили уведомления")
                status_level = "ATTENTION"
        else:
            # Если нет информации о последнем уведомлении
            reasons.append("Нет информации о последнем уведомлении")
            status_level = "ATTENTION"
        
        # Если нет причин для ATTENTION или ERROR, статус остается SUCCESS
        if not reasons:
            reasons.append("Все системы работают нормально")
        
        return status_level, reasons
    
    @staticmethod
    def get_status_display(status_level):
        """
        Возвращает человекочитаемое описание статуса
        """
        status_display = {
            'SUCCESS': '✅ Всё хорошо',
            'ATTENTION': '⚠️ Требуется внимание', 
            'ERROR': '❌ Критическая ошибка'
        }
        return status_display.get(status_level, '❓ Неизвестный статус')
