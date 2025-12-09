"""
Конфигурация pytest для проекта
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import Profile
from core.models import Dish, DailyGoal, Meal
from subscriptions.models import SubscriptionPlan, Subscription, Payment
from datetime import date, timedelta
from decimal import Decimal

User = get_user_model()


@pytest.fixture(autouse=True)
def clear_cache():
    """Автоматически очищает кэш перед каждым тестом для правильной работы throttling"""
    from django.core.cache import cache
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client():
    """Фикстура для API клиента"""
    return APIClient()


@pytest.fixture
def test_user():
    """Фикстура для создания тестового пользователя"""
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    Profile.objects.create(user=user, first_name='Test')
    return user


@pytest.fixture
def user(test_user):
    """Алиас для фикстуры test_user (для совместимости со старыми тестами)"""
    return test_user


@pytest.fixture
def user2():
    """Фикстура для создания второго тестового пользователя"""
    user = User.objects.create_user(
        username='testuser2',
        email='test2@example.com',
        password='testpass123'
    )
    Profile.objects.create(user=user, first_name='Test2')
    return user


@pytest.fixture
def authenticated_client(api_client, test_user):
    """Фикстура для аутентифицированного клиента"""
    refresh = RefreshToken.for_user(test_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def meal(user):
    """Фикстура для создания приёма пищи"""
    return Meal.objects.create(
        user=user,
        date=date.today(),
        meal_type='breakfast'
    )


@pytest.fixture
def dish(user, meal):
    """Фикстура для создания блюда"""
    return Dish.objects.create(
        user=user,
        meal=meal,
        name='Test Dish',
        weight=100,
        calories=200,
        proteins=Decimal('10.50'),
        fats=Decimal('5.25'),
        carbohydrates=Decimal('20.00')
    )


@pytest.fixture
def daily_goal(user):
    """Фикстура для создания цели на день"""
    return DailyGoal.objects.create(
        user=user,
        date=date.today(),
        calories=2000,
        proteins=Decimal('150.00'),
        fats=Decimal('66.67'),
        carbohydrates=Decimal('200.00'),
        is_auto_calculated=False
    )


@pytest.fixture
def subscription_plan():
    """Фикстура для создания тарифного плана"""
    return SubscriptionPlan.objects.create(
        name='Базовый',
        price_monthly=Decimal('299.00'),
        price_yearly=Decimal('2990.00'),
        features='Базовый функционал',
        is_active=True
    )


@pytest.fixture
def subscription(user, subscription_plan):
    """Фикстура для создания подписки"""
    return Subscription.objects.create(
        user=user,
        plan=subscription_plan,
        status='active',
        start_date=date.today(),
        end_date=date.today() + timedelta(days=30),
        auto_renew=True
    )

