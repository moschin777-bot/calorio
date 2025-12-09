from rest_framework import status, permissions, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.conf import settings
from .models import Subscription, SubscriptionPlan, Payment
from .serializers import (
    SubscriptionSerializer, 
    SubscriptionPlanSerializer,
    PaymentSerializer,
    CreatePaymentSerializer
)
from datetime import datetime, timedelta
from django.utils import timezone
import logging
import hmac
import hashlib
import json

logger = logging.getLogger(__name__)


class SubscriptionView(APIView):
    """
    API для получения информации о подписке
    GET /api/subscription/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Получение информации о текущей подписке пользователя"""
        # Получаем или создаём подписку пользователя
        subscription, created = Subscription.objects.select_related('plan').get_or_create(
            user=request.user,
            defaults={
                'plan': self._get_default_plan(),
                'status': 'expired',
            }
        )
        
        serializer = SubscriptionSerializer(subscription)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def _get_default_plan(self):
        """Получение базового тарифного плана"""
        # Создаём базовый план, если его нет
        plan, created = SubscriptionPlan.objects.get_or_create(
            name='Базовый',
            defaults={
                'price_monthly': 299.00,
                'price_yearly': 2990.00,
                'features': 'Базовый функционал',
                'is_active': True,
            }
        )
        return plan


class SubscriptionPlansView(generics.ListAPIView):
    """
    API для получения списка доступных тарифных планов
    GET /api/subscription/plans/
    """
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.AllowAny]


class PayMonthlyView(APIView):
    """
    API для оплаты месячной подписки
    POST /api/subscription/pay-monthly/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Создание платежа для месячной подписки"""
        serializer = CreatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        plan_id = serializer.validated_data.get('plan_id')
        
        # Получаем тарифный план
        if plan_id:
            plan = get_object_or_404(SubscriptionPlan, id=plan_id, is_active=True)
        else:
            # Используем базовый план
            plan, _ = SubscriptionPlan.objects.get_or_create(
                name='Базовый',
                defaults={
                    'price_monthly': 299.00,
                    'price_yearly': 2990.00,
                    'features': 'Базовый функционал',
                    'is_active': True,
                }
            )
        
        # Получаем или создаём подписку
        subscription, _ = Subscription.objects.get_or_create(
            user=request.user,
            defaults={
                'plan': plan,
                'status': 'expired',
            }
        )
        
        # Создаём платёж
        payment = Payment.objects.create(
            user=request.user,
            subscription=subscription,
            amount=plan.price_monthly,
            payment_type='monthly',
            status='pending',
            payment_provider='mock',  # В реальном приложении здесь будет реальный провайдер
        )
        
        # В реальном приложении здесь будет интеграция с платёжным провайдером
        # Для демонстрации возвращаем mock URL
        payment_url = f"https://payment-provider.example.com/pay/{payment.id}"
        
        return Response({
            'payment_id': payment.id,
            'amount': float(payment.amount),
            'payment_url': payment_url,
            'status': payment.status,
        }, status=status.HTTP_200_OK)


class PayYearlyView(APIView):
    """
    API для оплаты годовой подписки
    POST /api/subscription/pay-yearly/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Создание платежа для годовой подписки"""
        serializer = CreatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        plan_id = serializer.validated_data.get('plan_id')
        
        # Получаем тарифный план
        if plan_id:
            plan = get_object_or_404(SubscriptionPlan, id=plan_id, is_active=True)
        else:
            # Используем базовый план
            plan, _ = SubscriptionPlan.objects.get_or_create(
                name='Базовый',
                defaults={
                    'price_monthly': 299.00,
                    'price_yearly': 2990.00,
                    'features': 'Базовый функционал',
                    'is_active': True,
                }
            )
        
        # Получаем или создаём подписку
        subscription, _ = Subscription.objects.get_or_create(
            user=request.user,
            defaults={
                'plan': plan,
                'status': 'expired',
            }
        )
        
        # Создаём платёж
        payment = Payment.objects.create(
            user=request.user,
            subscription=subscription,
            amount=plan.price_yearly,
            payment_type='yearly',
            status='pending',
            payment_provider='mock',
        )
        
        # В реальном приложении здесь будет интеграция с платёжным провайдером
        payment_url = f"https://payment-provider.example.com/pay/{payment.id}"
        
        return Response({
            'payment_id': payment.id,
            'amount': float(payment.amount),
            'payment_url': payment_url,
            'status': payment.status,
        }, status=status.HTTP_200_OK)


class DisableAutoRenewView(APIView):
    """
    API для отключения автопродления подписки
    POST /api/subscription/disable-auto-renew/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Отключение автопродления"""
        subscription = get_object_or_404(Subscription, user=request.user)
        subscription.auto_renew = False
        subscription.save()
        
        return Response({
            'detail': 'Автопродление отключено.',
            'auto_renew': False,
        }, status=status.HTTP_200_OK)


class EnableAutoRenewView(APIView):
    """
    API для включения автопродления подписки
    POST /api/subscription/enable-auto-renew/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Включение автопродления"""
        subscription = get_object_or_404(Subscription, user=request.user)
        subscription.auto_renew = True
        subscription.save()
        
        return Response({
            'detail': 'Автопродление включено.',
            'auto_renew': True,
        }, status=status.HTTP_200_OK)


class PaymentHistoryPagination(PageNumberPagination):
    """Пагинация для истории платежей"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class PaymentHistoryView(generics.ListAPIView):
    """
    API для получения истории платежей
    GET /api/subscription/payments/
    """
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = PaymentHistoryPagination
    
    def get_queryset(self):
        """Получение платежей текущего пользователя"""
        return Payment.objects.filter(
            user=self.request.user
        ).select_related('subscription__plan').order_by('-created_at')


class WebhookView(APIView):
    """
    API для обработки webhook от платёжного провайдера
    POST /api/subscription/webhook/
    
    Требует проверки подписи для безопасности.
    """
    permission_classes = [permissions.AllowAny]  # Webhook не требует аутентификации
    
    def _verify_webhook_signature(self, request):
        """
        Проверка подписи webhook запроса.
        Использует HMAC-SHA256 для проверки подлинности запроса.
        
        Формат: заголовок X-Webhook-Signature содержит подпись в формате sha256=...
        """
        webhook_secret = settings.PAYMENT_WEBHOOK_SECRET
        
        # Если секрет не настроен, логируем предупреждение, но разрешаем в development
        if not webhook_secret:
            if settings.DEBUG:
                logger.warning("PAYMENT_WEBHOOK_SECRET not set, skipping signature verification in DEBUG mode")
                return True
            else:
                logger.error("PAYMENT_WEBHOOK_SECRET not set in production!")
                return False
        
        # Получаем подпись из заголовка
        signature_header = request.META.get('HTTP_X_WEBHOOK_SIGNATURE', '')
        if not signature_header:
            logger.warning("Webhook signature header missing")
            return False
        
        # Извлекаем подпись (формат: sha256=...)
        if '=' in signature_header:
            signature = signature_header.split('=')[1]
        else:
            signature = signature_header
        
        # Получаем тело запроса
        body = request.body
        
        # Вычисляем ожидаемую подпись
        expected_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()
        
        # Сравниваем подписи безопасным способом (защита от timing attacks)
        return hmac.compare_digest(signature, expected_signature)
    
    def post(self, request):
        """Обработка webhook от платёжного провайдера с проверкой подписи"""
        # Проверяем подпись запроса
        if not self._verify_webhook_signature(request):
            logger.warning(f"Invalid webhook signature from IP: {self._get_client_ip(request)}")
            return Response(
                {'status': 'error', 'message': 'Invalid signature'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            # Пример обработки (нужно адаптировать под конкретный провайдер)
            transaction_id = request.data.get('transaction_id')
            status_value = request.data.get('status')
            amount = request.data.get('amount')
            
            if not transaction_id:
                logger.warning("Webhook request missing transaction_id")
                return Response(
                    {'status': 'error', 'message': 'transaction_id required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Находим платёж по transaction_id
            payment = Payment.objects.filter(transaction_id=transaction_id).first()
            
            if not payment:
                logger.warning(f"Payment with transaction_id {transaction_id} not found")
                # Возвращаем 200, чтобы провайдер не повторял запрос
                return Response({'status': 'ok'}, status=status.HTTP_200_OK)
            
            # Валидация суммы платежа (защита от подделки)
            if amount and float(amount) != float(payment.amount):
                logger.error(
                    f"Amount mismatch for payment {payment.id}: "
                    f"expected {payment.amount}, got {amount}"
                )
                return Response(
                    {'status': 'error', 'message': 'Amount mismatch'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Обновляем статус платежа
            if status_value == 'completed':
                # Проверяем, что платёж ещё не был обработан
                if payment.status == 'completed':
                    logger.info(f"Payment {payment.id} already completed, skipping")
                    return Response({'status': 'ok'}, status=status.HTTP_200_OK)
                
                payment.status = 'completed'
                payment.save()
                
                # Активируем подписку
                subscription = payment.subscription
                subscription.status = 'active'
                subscription.start_date = timezone.now()
                
                # Устанавливаем дату окончания в зависимости от типа подписки
                if payment.payment_type == 'monthly':
                    subscription.end_date = timezone.now() + timedelta(days=30)
                elif payment.payment_type == 'yearly':
                    subscription.end_date = timezone.now() + timedelta(days=365)
                
                subscription.save()
                
                logger.info(
                    f"Payment {payment.id} completed, subscription {subscription.id} activated. "
                    f"User: {payment.user.email}"
                )
            elif status_value == 'failed':
                payment.status = 'failed'
                payment.save()
                logger.info(f"Payment {payment.id} failed")
            
            return Response({'status': 'ok'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error processing webhook: {e}", exc_info=True)
            return Response(
                {'status': 'error', 'message': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_client_ip(self, request):
        """Получение IP адреса клиента"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

