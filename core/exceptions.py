"""
Кастомные исключения для приложения
"""
from rest_framework.exceptions import APIException
from rest_framework import status


class SubscriptionExpiredException(APIException):
    """Исключение для истёкшей подписки"""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'Ваша подписка истекла. Пожалуйста, продлите подписку.'
    default_code = 'subscription_expired'


class InvalidImageException(APIException):
    """Исключение для невалидного изображения"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Неверный формат изображения.'
    default_code = 'invalid_image'


class RecognitionServiceUnavailableException(APIException):
    """Исключение для недоступного сервиса распознавания"""
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'Сервис распознавания временно недоступен.'
    default_code = 'recognition_service_unavailable'


class PaymentProviderException(APIException):
    """Исключение для ошибок платёжного провайдера"""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'Ошибка при обработке платежа. Попробуйте позже.'
    default_code = 'payment_provider_error'

