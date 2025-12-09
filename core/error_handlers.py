"""
Глобальные обработчики ошибок
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging
import re

logger = logging.getLogger(__name__)


def mask_sensitive_data(data):
    """
    Маскирует чувствительные данные в логах.
    Заменяет пароли, токены и другие секреты на ***
    """
    if not isinstance(data, (dict, str)):
        return data
    
    sensitive_fields = [
        'password', 'token', 'secret', 'api_key', 'access_token', 
        'refresh_token', 'authorization', 'auth'
    ]
    
    if isinstance(data, str):
        # Маскируем токены в строках
        data = re.sub(r'(Bearer\s+)([A-Za-z0-9\-_\.]+)', r'\1***', data)
        data = re.sub(r'(password["\']?\s*[:=]\s*["\']?)([^"\']+)', r'\1***', data, flags=re.IGNORECASE)
        return data
    
    masked_data = {}
    for key, value in data.items():
        key_lower = key.lower()
        # Проверяем, является ли поле чувствительным
        if any(sensitive in key_lower for sensitive in sensitive_fields):
            masked_data[key] = '***'
        elif isinstance(value, dict):
            masked_data[key] = mask_sensitive_data(value)
        elif isinstance(value, str) and len(value) > 50:
            # Маскируем длинные строки, которые могут быть токенами
            if 'token' in key_lower or 'key' in key_lower:
                masked_data[key] = '***'
            else:
                masked_data[key] = value
        else:
            masked_data[key] = value
    
    return masked_data


def custom_exception_handler(exc, context):
    """
    Кастомный обработчик исключений для REST API
    
    Обрабатывает все исключения и возвращает единообразный формат ответа
    """
    # Вызываем стандартный обработчик DRF
    response = exception_handler(exc, context)
    
    # Если стандартный обработчик вернул ответ, используем его
    if response is not None:
        # Маскируем чувствительные данные перед логированием
        safe_data = mask_sensitive_data(response.data) if hasattr(response, 'data') else None
        
        # Логируем ошибку без чувствительных данных
        logger.warning(
            f"API Error: {exc.__class__.__name__} - "
            f"Status: {response.status_code} - "
            f"View: {context.get('view', 'Unknown')} - "
            f"Data: {safe_data}"
        )
        
        # Форматируем ответ в единообразный формат
        custom_response_data = {}
        
        # Если это ошибка валидации (400), сохраняем структуру полей
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            custom_response_data = response.data
        # Для других ошибок используем единый формат
        else:
            if isinstance(response.data, dict):
                # Если есть поле 'detail', используем его
                if 'detail' in response.data:
                    custom_response_data = response.data
                else:
                    # Иначе оборачиваем в 'detail'
                    custom_response_data = {'detail': response.data}
            else:
                custom_response_data = {'detail': str(response.data)}
        
        response.data = custom_response_data
        
        return response
    
    # Если стандартный обработчик не вернул ответ (необработанное исключение)
    # Логируем критическую ошибку (без деталей запроса для безопасности)
    logger.error(
        f"Unhandled Exception: {exc.__class__.__name__} - "
        f"View: {context.get('view', 'Unknown')}",
        exc_info=True
    )
    
    # Возвращаем общую ошибку сервера
    return Response(
        {'detail': 'Внутренняя ошибка сервера. Попробуйте позже.'},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


def handle_404(request, exception=None):
    """Обработчик для 404 ошибок"""
    return Response(
        {'detail': 'Ресурс не найден.'},
        status=status.HTTP_404_NOT_FOUND
    )


def handle_500(request):
    """Обработчик для 500 ошибок"""
    logger.error(f"Server Error 500 for request: {request.path}")
    return Response(
        {'detail': 'Внутренняя ошибка сервера. Попробуйте позже.'},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )

