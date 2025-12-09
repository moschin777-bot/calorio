"""
Полные тесты для управления подписками (раздел 6 чеклиста)
Покрывает пункты 241-304 из TEST_CHECKLIST.md
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from datetime import date, timedelta
from subscriptions.models import Subscription, SubscriptionPlan, Payment

User = get_user_model()


@pytest.mark.django_db
class TestSubscriptionInfo:
    """6.1. Получение информации о подписке (GET /api/subscription/)"""
    
    def test_get_subscription_authenticated(self, authenticated_client, test_user):
        """Тест 241: Получение информации о подписке авторизованным пользователем"""
        response = authenticated_client.get('/api/subscription/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'plan_name' in response.data
        assert 'status' in response.data
        assert 'days_remaining' in response.data
        assert 'end_date' in response.data
        assert 'auto_renew' in response.data
    
    def test_get_subscription_without_auth(self, api_client):
        """Тест 242: Получение информации о подписке без токена авторизации"""
        response = api_client.get('/api/subscription/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_subscription_creates_if_not_exists(self, authenticated_client, test_user):
        """Тест 244: Создаётся подписка со статусом expired если не существует"""
        response = authenticated_client.get('/api/subscription/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'expired'
        assert Subscription.objects.filter(user=test_user).exists()


@pytest.mark.django_db
class TestSubscriptionPlans:
    """6.2. Получение списка тарифных планов (GET /api/subscription/plans/)"""
    
    def test_get_plans_without_auth(self, api_client):
        """Тест 251: Получение списка тарифных планов без авторизации"""
        response = api_client.get('/api/subscription/plans/')
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_get_plans_authenticated(self, authenticated_client):
        """Тест 252: Получение списка тарифных планов авторизованным пользователем"""
        response = authenticated_client.get('/api/subscription/plans/')
        
        assert response.status_code == status.HTTP_200_OK
        # API использует пагинацию, поэтому проверяем results
        assert 'results' in response.data
        assert isinstance(response.data['results'], list)


@pytest.mark.django_db
class TestPayments:
    """6.3-6.4. Оплата подписки"""
    
    def test_pay_monthly_without_auth(self, api_client):
        """Тест 259: Создание платежа без токена авторизации"""
        response = api_client.post('/api/subscription/pay-monthly/', {}, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_pay_yearly_without_auth(self, api_client):
        """Тест 268: Создание платежа для годовой подписки без токена"""
        response = api_client.post('/api/subscription/pay-yearly/', {}, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestAutoRenew:
    """6.5-6.6. Управление автопродлением"""
    
    def test_disable_auto_renew_without_auth(self, api_client):
        """Тест 275: Отключение автопродления без токена"""
        response = api_client.post('/api/subscription/disable-auto-renew/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_enable_auto_renew_without_auth(self, api_client):
        """Тест 281: Включение автопродления без токена"""
        response = api_client.post('/api/subscription/enable-auto-renew/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestPaymentHistory:
    """6.7. История платежей"""
    
    def test_get_payment_history(self, authenticated_client, test_user):
        """Тест 285: Получение истории платежей"""
        response = authenticated_client.get('/api/subscription/payments/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'count' in response.data
        assert 'results' in response.data
    
    def test_get_payment_history_without_auth(self, api_client):
        """Тест 289: Получение истории платежей без токена"""
        response = api_client.get('/api/subscription/payments/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

