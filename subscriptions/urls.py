from django.urls import path
from .views import (
    SubscriptionView,
    SubscriptionPlansView,
    PayMonthlyView,
    PayYearlyView,
    DisableAutoRenewView,
    EnableAutoRenewView,
    PaymentHistoryView,
    WebhookView,
)

app_name = 'subscriptions'

urlpatterns = [
    # Информация о подписке
    path('subscription/', SubscriptionView.as_view(), name='subscription'),
    path('subscription/plans/', SubscriptionPlansView.as_view(), name='subscription-plans'),
    
    # Оплата
    path('subscription/pay-monthly/', PayMonthlyView.as_view(), name='pay-monthly'),
    path('subscription/pay-yearly/', PayYearlyView.as_view(), name='pay-yearly'),
    
    # Управление автопродлением
    path('subscription/disable-auto-renew/', DisableAutoRenewView.as_view(), name='disable-auto-renew'),
    path('subscription/enable-auto-renew/', EnableAutoRenewView.as_view(), name='enable-auto-renew'),
    
    # История платежей
    path('subscription/payments/', PaymentHistoryView.as_view(), name='payment-history'),
    
    # Webhook
    path('subscription/webhook/', WebhookView.as_view(), name='webhook'),
]

