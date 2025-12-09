"""
Полные тесты для управления днями (раздел 5 чеклиста)
Покрывает пункты 223-240 из TEST_CHECKLIST.md
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from datetime import date
from core.models import DailyGoal, Meal, Dish

User = get_user_model()


@pytest.mark.django_db
class TestDayData:
    """5.1. Получение данных за день (GET /api/days/{date}/)"""
    
    def test_get_day_with_goal_and_dishes(self, authenticated_client, test_user):
        """Тест 223: Получение данных за день с установленной целью и блюдами"""
        test_date = date.today()
        
        # Создаём цель
        goal = DailyGoal.objects.create(
            user=test_user,
            date=test_date,
            calories=2000,
            proteins=150.0,
            fats=70.0,
            carbohydrates=250.0
        )
        
        # Создаём блюда
        meal_breakfast = Meal.objects.create(
            user=test_user,
            date=test_date,
            meal_type='breakfast'
        )
        Dish.objects.create(
            user=test_user,
            meal=meal_breakfast,
            name='Овсянка',
            weight=200,
            calories=300,
            proteins=10.0,
            fats=5.0,
            carbohydrates=50.0
        )
        
        response = authenticated_client.get(f'/api/days/{test_date}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'date' in response.data
        assert 'goal' in response.data
        assert 'meals' in response.data
        assert 'summary' in response.data
        assert response.data['goal']['calories'] == 2000
        assert len(response.data['meals']['breakfast']) == 1
    
    def test_get_day_without_goal(self, authenticated_client, test_user):
        """Тест 224: Получение данных за день без установленной цели"""
        test_date = date.today()
        
        response = authenticated_client.get(f'/api/days/{test_date}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['goal'] is None
    
    def test_get_day_without_dishes(self, authenticated_client):
        """Тест 225: Получение данных за день без блюд"""
        test_date = date.today()
        
        response = authenticated_client.get(f'/api/days/{test_date}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['meals']['breakfast'] == []
        assert response.data['meals']['lunch'] == []
        assert response.data['meals']['dinner'] == []
        assert response.data['meals']['snack'] == []
    
    def test_get_day_breakfast_only(self, authenticated_client, test_user):
        """Тест 226: Получение данных за день с блюдами только в breakfast"""
        test_date = date.today()
        
        meal = Meal.objects.create(
            user=test_user,
            date=test_date,
            meal_type='breakfast'
        )
        Dish.objects.create(
            user=test_user,
            meal=meal,
            name='Яйца',
            weight=100,
            calories=150,
            proteins=12.0,
            fats=10.0,
            carbohydrates=1.0
        )
        
        response = authenticated_client.get(f'/api/days/{test_date}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['meals']['breakfast']) == 1
        assert len(response.data['meals']['lunch']) == 0
        assert len(response.data['meals']['dinner']) == 0
        assert len(response.data['meals']['snack']) == 0
    
    def test_get_day_lunch_only(self, authenticated_client, test_user):
        """Тест 227: Получение данных за день с блюдами только в lunch"""
        test_date = date.today()
        
        meal = Meal.objects.create(
            user=test_user,
            date=test_date,
            meal_type='lunch'
        )
        Dish.objects.create(
            user=test_user,
            meal=meal,
            name='Курица с рисом',
            weight=300,
            calories=500,
            proteins=40.0,
            fats=15.0,
            carbohydrates=60.0
        )
        
        response = authenticated_client.get(f'/api/days/{test_date}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['meals']['lunch']) == 1
        assert len(response.data['meals']['breakfast']) == 0
    
    def test_get_day_all_meal_types(self, authenticated_client, test_user):
        """Тест 230: Получение данных за день с блюдами во всех типах приёмов пищи"""
        test_date = date.today()
        
        for meal_type in ['breakfast', 'lunch', 'dinner', 'snack']:
            meal = Meal.objects.create(
                user=test_user,
                date=test_date,
                meal_type=meal_type
            )
            Dish.objects.create(
                user=test_user,
                meal=meal,
                name=f'Блюдо {meal_type}',
                weight=100,
                calories=100,
                proteins=10.0,
                fats=5.0,
                carbohydrates=10.0
            )
        
        response = authenticated_client.get(f'/api/days/{test_date}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['meals']['breakfast']) == 1
        assert len(response.data['meals']['lunch']) == 1
        assert len(response.data['meals']['dinner']) == 1
        assert len(response.data['meals']['snack']) == 1
    
    def test_get_day_invalid_date_format(self, authenticated_client):
        """Тест 231: Получение данных за день с некорректным форматом date"""
        response = authenticated_client.get('/api/days/invalid-date/')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_get_day_without_auth(self, api_client):
        """Тест 232: Получение данных за день без токена авторизации"""
        test_date = date.today()
        response = api_client.get(f'/api/days/{test_date}/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_day_invalid_token(self, api_client):
        """Тест 233: Получение данных за день с невалидным токеном"""
        api_client.credentials(HTTP_AUTHORIZATION='Bearer invalid-token')
        test_date = date.today()
        response = api_client.get(f'/api/days/{test_date}/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_day_response_structure(self, authenticated_client):
        """Тест 234: Проверка структуры ответа"""
        test_date = date.today()
        response = authenticated_client.get(f'/api/days/{test_date}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'date' in response.data
        assert 'goal' in response.data
        assert 'meals' in response.data
        assert 'summary' in response.data
        
        assert 'breakfast' in response.data['meals']
        assert 'lunch' in response.data['meals']
        assert 'dinner' in response.data['meals']
        assert 'snack' in response.data['meals']
    
    def test_get_day_summary_fields(self, authenticated_client):
        """Тест 235: Проверка, что в summary есть нужные поля"""
        test_date = date.today()
        response = authenticated_client.get(f'/api/days/{test_date}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'total_calories' in response.data['summary']
        assert 'total_proteins' in response.data['summary']
        assert 'total_fats' in response.data['summary']
        assert 'total_carbohydrates' in response.data['summary']
        assert 'goal_progress' in response.data['summary']
    
    def test_get_day_goal_progress_fields(self, authenticated_client):
        """Тест 236: Проверка, что в goal_progress есть нужные поля"""
        test_date = date.today()
        response = authenticated_client.get(f'/api/days/{test_date}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'calories_percent' in response.data['summary']['goal_progress']
        assert 'proteins_percent' in response.data['summary']['goal_progress']
        assert 'fats_percent' in response.data['summary']['goal_progress']
        assert 'carbohydrates_percent' in response.data['summary']['goal_progress']
    
    def test_get_day_correct_totals_calculation(self, authenticated_client, test_user):
        """Тест 237: Проверка корректности расчёта суммарных значений КБЖУ"""
        test_date = date.today()
        
        meal = Meal.objects.create(
            user=test_user,
            date=test_date,
            meal_type='breakfast'
        )
        
        # Создаём 3 блюда с известными значениями
        Dish.objects.create(
            user=test_user,
            meal=meal,
            name='Блюдо 1',
            weight=100,
            calories=100,
            proteins=10.0,
            fats=5.0,
            carbohydrates=15.0
        )
        Dish.objects.create(
            user=test_user,
            meal=meal,
            name='Блюдо 2',
            weight=100,
            calories=200,
            proteins=20.0,
            fats=10.0,
            carbohydrates=25.0
        )
        Dish.objects.create(
            user=test_user,
            meal=meal,
            name='Блюдо 3',
            weight=100,
            calories=300,
            proteins=30.0,
            fats=15.0,
            carbohydrates=35.0
        )
        
        response = authenticated_client.get(f'/api/days/{test_date}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['summary']['total_calories'] == 600
        assert float(response.data['summary']['total_proteins']) == 60.0
        assert float(response.data['summary']['total_fats']) == 30.0
        assert float(response.data['summary']['total_carbohydrates']) == 75.0
    
    def test_get_day_correct_goal_progress(self, authenticated_client, test_user):
        """Тест 238: Проверка корректности расчёта процентов выполнения целей"""
        test_date = date.today()
        
        # Создаём цель
        DailyGoal.objects.create(
            user=test_user,
            date=test_date,
            calories=1000,
            proteins=100.0,
            fats=50.0,
            carbohydrates=100.0
        )
        
        # Создаём блюдо на 50% от цели
        meal = Meal.objects.create(
            user=test_user,
            date=test_date,
            meal_type='breakfast'
        )
        Dish.objects.create(
            user=test_user,
            meal=meal,
            name='Блюдо',
            weight=100,
            calories=500,
            proteins=50.0,
            fats=25.0,
            carbohydrates=50.0
        )
        
        response = authenticated_client.get(f'/api/days/{test_date}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert float(response.data['summary']['goal_progress']['calories_percent']) == 50.0
        assert float(response.data['summary']['goal_progress']['proteins_percent']) == 50.0
        assert float(response.data['summary']['goal_progress']['fats_percent']) == 50.0
        assert float(response.data['summary']['goal_progress']['carbohydrates_percent']) == 50.0
    
    def test_get_day_goal_progress_zero_without_goal(self, authenticated_client, test_user):
        """Тест 239: Проверка, что проценты = 0, если цель не установлена"""
        test_date = date.today()
        
        # Создаём блюдо без цели
        meal = Meal.objects.create(
            user=test_user,
            date=test_date,
            meal_type='breakfast'
        )
        Dish.objects.create(
            user=test_user,
            meal=meal,
            name='Блюдо',
            weight=100,
            calories=500,
            proteins=50.0,
            fats=25.0,
            carbohydrates=50.0
        )
        
        response = authenticated_client.get(f'/api/days/{test_date}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert float(response.data['summary']['goal_progress']['calories_percent']) == 0.0
        assert float(response.data['summary']['goal_progress']['proteins_percent']) == 0.0
        assert float(response.data['summary']['goal_progress']['fats_percent']) == 0.0
        assert float(response.data['summary']['goal_progress']['carbohydrates_percent']) == 0.0
    
    def test_get_day_only_own_dishes(self, authenticated_client, test_user):
        """Тест 240: Проверка, что возвращаются только блюда текущего пользователя"""
        test_date = date.today()
        
        # Создаём другого пользователя
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        # Создаём блюдо для текущего пользователя
        meal1 = Meal.objects.create(
            user=test_user,
            date=test_date,
            meal_type='breakfast'
        )
        Dish.objects.create(
            user=test_user,
            meal=meal1,
            name='Моё блюдо',
            weight=100,
            calories=100,
            proteins=10.0,
            fats=5.0,
            carbohydrates=10.0
        )
        
        # Создаём блюдо для другого пользователя
        meal2 = Meal.objects.create(
            user=other_user,
            date=test_date,
            meal_type='breakfast'
        )
        Dish.objects.create(
            user=other_user,
            meal=meal2,
            name='Чужое блюдо',
            weight=100,
            calories=200,
            proteins=20.0,
            fats=10.0,
            carbohydrates=20.0
        )
        
        response = authenticated_client.get(f'/api/days/{test_date}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['meals']['breakfast']) == 1
        assert response.data['meals']['breakfast'][0]['name'] == 'Моё блюдо'
        assert response.data['summary']['total_calories'] == 100

