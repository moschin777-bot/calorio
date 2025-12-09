"""
Health check views для мониторинга состояния приложения
"""
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


def health_check(request):
    """
    Health check эндпоинт для проверки работоспособности приложения.
    Проверяет доступность базы данных и кэша.
    
    Возвращает:
    - 200 OK если все компоненты работают
    - 503 Service Unavailable если какой-то компонент недоступен
    """
    health_status = {
        'status': 'healthy',
        'components': {}
    }
    
    # Проверка базы данных
    try:
        connection.ensure_connection()
        health_status['components']['database'] = 'healthy'
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        health_status['status'] = 'unhealthy'
        health_status['components']['database'] = 'unhealthy'
    
    # Проверка кэша
    try:
        cache.set('health_check', 'ok', 10)
        cache_value = cache.get('health_check')
        if cache_value == 'ok':
            health_status['components']['cache'] = 'healthy'
        else:
            health_status['components']['cache'] = 'unhealthy'
            health_status['status'] = 'unhealthy'
    except Exception as e:
        logger.error(f"Cache health check failed: {str(e)}")
        health_status['status'] = 'unhealthy'
        health_status['components']['cache'] = 'unhealthy'
    
    # Определение HTTP статуса
    status_code = 200 if health_status['status'] == 'healthy' else 503
    
    return JsonResponse(health_status, status=status_code)


def readiness_check(request):
    """
    Readiness check эндпоинт для Kubernetes.
    Проверяет, готово ли приложение принимать запросы.
    
    Возвращает:
    - 200 OK если приложение готово
    - 503 Service Unavailable если приложение не готово
    """
    # Простая проверка - приложение всегда готово, если запущено
    # Можно добавить дополнительные проверки (миграции, инициализация и т.д.)
    return JsonResponse({'status': 'ready'}, status=200)


def liveness_check(request):
    """
    Liveness check эндпоинт для Kubernetes.
    Проверяет, что приложение живо и не зависло.
    
    Возвращает:
    - 200 OK всегда (если приложение отвечает, значит оно живо)
    """
    return JsonResponse({'status': 'alive'}, status=200)

