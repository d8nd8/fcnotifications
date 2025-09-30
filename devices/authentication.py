from rest_framework import authentication, exceptions
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from .models import Device


class XTokenAuthentication(authentication.BaseAuthentication):
    """
    Custom authentication class that uses X-TOKEN header to authenticate devices.
    """
    
    def authenticate(self, request):
        token = request.META.get('HTTP_X_TOKEN')
        
        if not token:
            return None
            
        try:
            device = Device.objects.get(token=token)
            # Update last_seen when device authenticates
            device.last_seen = timezone.now()
            device.save(update_fields=['last_seen'])
            return (device, None)
        except Device.DoesNotExist:
            raise exceptions.AuthenticationFailed('Неверный токен')
        except ValueError:
            raise exceptions.AuthenticationFailed('Неверный формат токена')
    
    def authenticate_header(self, request):
        return 'X-TOKEN'
