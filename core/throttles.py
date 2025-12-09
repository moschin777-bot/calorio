from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.exceptions import Throttled
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta


class RegistrationThrottle(AnonRateThrottle):
    """
    Throttle для эндпоинта регистрации.
    Ограничения: 5 запросов в час с одного IP.
    """
    rate = '5/h'
    
    def get_cache_key(self, request, view):
        """Получаем ключ кэша на основе IP адреса"""
        ident = self.get_ident(request)
        return f'throttle_registration_{ident}'


class LoginThrottle(AnonRateThrottle):
    """
    Throttle для эндпоинта логина.
    Ограничения: 10 запросов в минуту с одного IP.
    """
    rate = '10/m'
    
    def get_cache_key(self, request, view):
        """Получаем ключ кэша на основе IP адреса"""
        ident = self.get_ident(request)
        return f'throttle_login_{ident}'


class DishRecognitionThrottle(AnonRateThrottle):
    """
    Кастомный throttle для endpoint распознавания блюд.
    Ограничения: 10 запросов в минуту и 100 запросов в день с одного IP.
    """
    rate = '10/minute'
    daily_rate = 100
    
    def get_cache_key(self, request, view):
        """Получаем ключ кэша на основе IP адреса"""
        ident = self.get_ident(request)
        return f'throttle_dish_recognition_{ident}'
    
    def allow_request(self, request, view):
        """
        Проверяем оба лимита: по минутам и по дням
        """
        # Получаем IP адрес
        ident = self.get_ident(request)
        
        # Проверяем лимит по минутам
        minute_key = f'throttle_dish_recognition_minute_{ident}'
        minute_history = cache.get(minute_key, [])
        
        # Удаляем старые записи (старше минуты)
        now = timezone.now()
        minute_history = [timestamp for timestamp in minute_history if now - timestamp < timedelta(minutes=1)]
        
        # Проверяем лимит по минутам
        if len(minute_history) >= 10:
            return False
        
        # Проверяем лимит по дням
        day_key = f'throttle_dish_recognition_day_{ident}'
        day_history = cache.get(day_key, [])
        
        # Удаляем старые записи (старше дня)
        day_history = [timestamp for timestamp in day_history if now - timestamp < timedelta(days=1)]
        
        # Проверяем лимит по дням
        if len(day_history) >= 100:
            return False
        
        # Если оба лимита не превышены, разрешаем запрос
        # Обновляем историю
        minute_history.append(now)
        day_history.append(now)
        
        # Сохраняем в кэш
        cache.set(minute_key, minute_history, timeout=60)  # 60 секунд
        cache.set(day_key, day_history, timeout=86400)  # 24 часа
        
        return True
    
    def wait(self):
        """
        Возвращаем время ожидания до следующего разрешенного запроса
        """
        # Возвращаем время до сброса минутного лимита
        return 60

