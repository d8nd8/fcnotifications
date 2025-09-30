import logging
from django.conf import settings
from telegram import Bot
from telegram.error import TelegramError
from .models import TelegramUser

logger = logging.getLogger(__name__)


def notify(text):
    """
    Send notification to all active Telegram users.
    Synchronous implementation for simplicity.
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not configured")
        return False
    
    try:
        # Convert Markdown to HTML for better formatting
        html_text = text.replace('**', '<b>').replace('**', '</b>')
        html_text = html_text.replace('*', '<i>').replace('*', '</i>')
        
        # Get all active users
        active_users = TelegramUser.objects.filter(is_active=True)
        total_users = active_users.count()
        
        if total_users == 0:
            logger.warning("No active users found for notifications")
            return False
        
        logger.info(f"Sending notification to {total_users} users")
        logger.info(f"Message text: {text[:100]}...")
        
        # Use synchronous requests for simplicity
        import requests
        
        success_count = 0
        error_count = 0
        
        for user in active_users:
            try:
                url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
                data = {
                    'chat_id': user.user_id,
                    'text': html_text,
                    'parse_mode': 'HTML'
                }
                
                response = requests.post(url, data=data, timeout=10)
                response.raise_for_status()
                
                success_count += 1
                logger.debug(f"Notification sent to user {user.user_id}")
                
            except requests.exceptions.RequestException as e:
                error_count += 1
                logger.warning(f"Failed to send to user {user.user_id}: {e}")
                
                # Если пользователь заблокировал бота, деактивируем его
                if "bot was blocked by the user" in str(e).lower() or "Forbidden" in str(e):
                    user.is_active = False
                    user.save()
                    logger.info(f"Deactivated user {user.user_id} (bot blocked)")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"Unexpected error sending to user {user.user_id}: {e}")
        
        logger.info(f"Notifications sent: {success_count} success, {error_count} errors")
        return success_count > 0
        
    except Exception as e:
        logger.error(f"Unexpected error in notification system: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        return False

