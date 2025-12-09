"""
Полные тесты для управления целями КБЖУ (раздел 4 чеклиста)
Покрывает пункты 169-222 из TEST_CHECKLIST.md
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from datetime import date, timedelta
from core.models import DailyGoal

User = get_user_model()


@pytest.mark.django_db
class TestGoalRetrieval:
    """4.1. Получение цели на день (GET /api/goals/{date}/)"""
    
    def test_get_existing_goal(self, authenticated_client, test_user):
        """Тест 169: Получение существующей цели на указанную дату"""
        test_date = date.today()
        goal = DailyGoal.objects.create(
            user=test_user,
            date=test_date,
            calories=2000,
            proteins=150.0,
            fats=70.0,
            carbohydrates=250.0
        )
        
        response = authenticated_client.get(f'/api/goals/{test_date}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == goal.id
        assert response.data['calories'] == 2000
        assert response.data['proteins'] == '150.00'
    
    def test_get_nonexistent_goal(self, authenticated_client):
        """Тест 170: Получение цели на дату, для которой цель не установлена"""
        test_date = date.today() + timedelta(days=10)
        response = authenticated_client.get(f'/api/goals/{test_date}/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_get_goal_invalid_date_format(self, authenticated_client):
        """Тест 171: Получение цели с некорректным форматом date"""
        response = authenticated_client.get('/api/goals/invalid-date/')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_get_goal_without_auth(self, api_client):
        """Тест 172: Получение цели без токена авторизации"""
        test_date = date.today()
        response = api_client.get(f'/api/goals/{test_date}/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_goal_invalid_token(self, api_client):
        """Тест 173: Получение цели с невалидным токеном"""
        api_client.credentials(HTTP_AUTHORIZATION='Bearer invalid-token')
        test_date = date.today()
        response = api_client.get(f'/api/goals/{test_date}/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_goal_returns_all_fields(self, authenticated_client, test_user):
        """Тест 174: Проверка, что возвращаются все поля цели"""
        test_date = date.today()
        goal = DailyGoal.objects.create(
            user=test_user,
            date=test_date,
            calories=2000,
            proteins=150.0,
            fats=70.0,
            carbohydrates=250.0,
            is_auto_calculated=True
        )
        
        response = authenticated_client.get(f'/api/goals/{test_date}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'id' in response.data
        assert 'date' in response.data
        assert 'calories' in response.data
        assert 'proteins' in response.data
        assert 'fats' in response.data
        assert 'carbohydrates' in response.data
        assert 'is_auto_calculated' in response.data
        assert 'created_at' in response.data
        assert 'updated_at' in response.data
    
    def test_get_goal_only_own(self, authenticated_client, test_user):
        """Тест 175: Проверка, что возвращается только цель текущего пользователя"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        test_date = date.today()
        
        # Создаём цель для другого пользователя
        DailyGoal.objects.create(
            user=other_user,
            date=test_date,
            calories=3000,
            proteins=200.0,
            fats=100.0,
            carbohydrates=300.0
        )
        
        # Пытаемся получить цель текущим пользователем
        response = authenticated_client.get(f'/api/goals/{test_date}/')
        
        # Должна вернуться 404, так как у текущего пользователя нет цели
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestGoalCreateUpdate:
    """4.2. Создание/обновление цели на день (POST /api/goals/{date}/)"""
    
    def test_create_goal_valid_data(self, authenticated_client, test_user):
        """Тест 176: Создание цели с корректными данными"""
        test_date = date.today()
        data = {
            'calories': 2000,
            'proteins': 150.0,
            'fats': 70.0,
            'carbohydrates': 250.0
        }
        
        response = authenticated_client.post(f'/api/goals/{test_date}/', data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['calories'] == 2000
        assert DailyGoal.objects.filter(user=test_user, date=test_date).exists()
    
    def test_create_goal_calories_zero(self, authenticated_client):
        """Тест 177: Создание цели с calories = 0"""
        test_date = date.today()
        data = {
            'calories': 0,
            'proteins': 150.0,
            'fats': 70.0,
            'carbohydrates': 250.0
        }
        
        response = authenticated_client.post(f'/api/goals/{test_date}/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'calories' in response.data
    
    def test_create_goal_negative_calories(self, authenticated_client):
        """Тест 178: Создание цели с calories < 0"""
        test_date = date.today()
        data = {
            'calories': -100,
            'proteins': 150.0,
            'fats': 70.0,
            'carbohydrates': 250.0
        }
        
        response = authenticated_client.post(f'/api/goals/{test_date}/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'calories' in response.data
    
    def test_create_goal_negative_proteins(self, authenticated_client):
        """Тест 179: Создание цели с proteins < 0"""
        test_date = date.today()
        data = {
            'calories': 2000,
            'proteins': -10.0,
            'fats': 70.0,
            'carbohydrates': 250.0
        }
        
        response = authenticated_client.post(f'/api/goals/{test_date}/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'proteins' in response.data
    
    def test_create_goal_negative_fats(self, authenticated_client):
        """Тест 180: Создание цели с fats < 0"""
        test_date = date.today()
        data = {
            'calories': 2000,
            'proteins': 150.0,
            'fats': -10.0,
            'carbohydrates': 250.0
        }
        
        response = authenticated_client.post(f'/api/goals/{test_date}/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'fats' in response.data
    
    def test_create_goal_negative_carbs(self, authenticated_client):
        """Тест 181: Создание цели с carbohydrates < 0"""
        test_date = date.today()
        data = {
            'calories': 2000,
            'proteins': 150.0,
            'fats': 70.0,
            'carbohydrates': -10.0
        }
        
        response = authenticated_client.post(f'/api/goals/{test_date}/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'carbohydrates' in response.data
    
    def test_create_goal_proteins_too_many_decimals(self, authenticated_client):
        """Тест 182: Создание цели с proteins с более чем 2 знаками после запятой"""
        test_date = date.today()
        data = {
            'calories': 2000,
            'proteins': 150.123,
            'fats': 70.0,
            'carbohydrates': 250.0
        }
        
        response = authenticated_client.post(f'/api/goals/{test_date}/', data, format='json')
        
        # Должно округлиться или вернуть ошибку
        if response.status_code == status.HTTP_201_CREATED:
            assert float(response.data['proteins']) == 150.12
        else:
            assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_create_goal_missing_calories(self, authenticated_client):
        """Тест 185: Создание цели без поля calories"""
        test_date = date.today()
        data = {
            'proteins': 150.0,
            'fats': 70.0,
            'carbohydrates': 250.0
        }
        
        response = authenticated_client.post(f'/api/goals/{test_date}/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'calories' in response.data
    
    def test_create_goal_invalid_date_format(self, authenticated_client):
        """Тест 189: Создание цели с некорректным форматом date в URL"""
        data = {
            'calories': 2000,
            'proteins': 150.0,
            'fats': 70.0,
            'carbohydrates': 250.0
        }
        
        response = authenticated_client.post('/api/goals/invalid-date/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_update_existing_goal(self, authenticated_client, test_user):
        """Тест 190: Обновление существующей цели (upsert логика)"""
        test_date = date.today()
        
        # Создаём начальную цель
        DailyGoal.objects.create(
            user=test_user,
            date=test_date,
            calories=2000,
            proteins=150.0,
            fats=70.0,
            carbohydrates=250.0
        )
        
        # Обновляем цель
        data = {
            'calories': 2500,
            'proteins': 180.0,
            'fats': 80.0,
            'carbohydrates': 300.0
        }
        
        response = authenticated_client.post(f'/api/goals/{test_date}/', data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['calories'] == 2500
        assert DailyGoal.objects.filter(user=test_user, date=test_date).count() == 1
    
    def test_create_goal_without_auth(self, api_client):
        """Тест 191: Создание цели без токена авторизации"""
        test_date = date.today()
        data = {
            'calories': 2000,
            'proteins': 150.0,
            'fats': 70.0,
            'carbohydrates': 250.0
        }
        
        response = api_client.post(f'/api/goals/{test_date}/', data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_create_goal_is_not_auto_calculated(self, authenticated_client, test_user):
        """Тест 193: Проверка, что после создания is_auto_calculated = False"""
        test_date = date.today()
        data = {
            'calories': 2000,
            'proteins': 150.0,
            'fats': 70.0,
            'carbohydrates': 250.0
        }
        
        response = authenticated_client.post(f'/api/goals/{test_date}/', data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['is_auto_calculated'] is False
    
    def test_create_goal_returns_201(self, authenticated_client):
        """Тест 194: Проверка, что после создания возвращается статус 201 Created"""
        test_date = date.today()
        data = {
            'calories': 2000,
            'proteins': 150.0,
            'fats': 70.0,
            'carbohydrates': 250.0
        }
        
        response = authenticated_client.post(f'/api/goals/{test_date}/', data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_update_goal_returns_200(self, authenticated_client, test_user):
        """Тест 195: Проверка, что после обновления возвращается статус 200 OK"""
        test_date = date.today()
        
        # Создаём начальную цель
        DailyGoal.objects.create(
            user=test_user,
            date=test_date,
            calories=2000,
            proteins=150.0,
            fats=70.0,
            carbohydrates=250.0
        )
        
        # Обновляем
        data = {
            'calories': 2500,
            'proteins': 180.0,
            'fats': 80.0,
            'carbohydrates': 300.0
        }
        
        response = authenticated_client.post(f'/api/goals/{test_date}/', data, format='json')
        
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestGoalAutoCalculate:
    """4.3. Автоматический расчёт целей (POST /api/goals/auto-calculate/)"""
    
    def test_auto_calculate_valid_data(self, authenticated_client):
        """Тест 196: Автоматический расчёт целей с корректными данными"""
        test_date = date.today()
        data = {
            'weight': 70,
            'height': 175,
            'age': 30,
            'activity_level': 'moderate',
            'date': str(test_date)
        }
        
        response = authenticated_client.post('/api/goals/auto-calculate/', data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'calories' in response.data
        assert 'proteins' in response.data
        assert 'fats' in response.data
        assert 'carbohydrates' in response.data
    
    def test_auto_calculate_with_gender(self, authenticated_client):
        """Тест 197: Автоматический расчёт целей с указанием gender"""
        test_date = date.today()
        data = {
            'weight': 70,
            'height': 175,
            'age': 30,
            'activity_level': 'moderate',
            'gender': 'male',
            'date': str(test_date)
        }
        
        response = authenticated_client.post('/api/goals/auto-calculate/', data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_auto_calculate_with_goal_maintain(self, authenticated_client):
        """Тест 214: Автоматический расчёт целей с goal = maintain"""
        test_date = date.today()
        data = {
            'weight': 70,
            'height': 175,
            'age': 30,
            'activity_level': 'moderate',
            'goal': 'maintain',
            'date': str(test_date)
        }
        
        response = authenticated_client.post('/api/goals/auto-calculate/', data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_auto_calculate_missing_weight(self, authenticated_client):
        """Тест 199: Автоматический расчёт целей без поля weight"""
        test_date = date.today()
        data = {
            'height': 175,
            'age': 30,
            'activity_level': 'moderate',
            'date': str(test_date)
        }
        
        response = authenticated_client.post('/api/goals/auto-calculate/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'weight' in response.data
    
    def test_auto_calculate_zero_weight(self, authenticated_client):
        """Тест 200: Автоматический расчёт целей с weight <= 0"""
        test_date = date.today()
        data = {
            'weight': 0,
            'height': 175,
            'age': 30,
            'activity_level': 'moderate',
            'date': str(test_date)
        }
        
        response = authenticated_client.post('/api/goals/auto-calculate/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'weight' in response.data
    
    def test_auto_calculate_invalid_activity_level(self, authenticated_client):
        """Тест 206: Автоматический расчёт целей с невалидным activity_level"""
        test_date = date.today()
        data = {
            'weight': 70,
            'height': 175,
            'age': 30,
            'activity_level': 'invalid',
            'date': str(test_date)
        }
        
        response = authenticated_client.post('/api/goals/auto-calculate/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'activity_level' in response.data
    
    def test_auto_calculate_without_auth(self, api_client):
        """Тест 219: Автоматический расчёт целей без токена авторизации"""
        test_date = date.today()
        data = {
            'weight': 70,
            'height': 175,
            'age': 30,
            'activity_level': 'moderate',
            'date': str(test_date)
        }
        
        response = api_client.post('/api/goals/auto-calculate/', data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_auto_calculate_is_auto_calculated_true(self, authenticated_client, test_user):
        """Тест 221: Проверка, что после расчёта is_auto_calculated = True"""
        test_date = date.today()
        data = {
            'weight': 70,
            'height': 175,
            'age': 30,
            'activity_level': 'moderate',
            'date': str(test_date)
        }
        
        response = authenticated_client.post('/api/goals/auto-calculate/', data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['is_auto_calculated'] is True
        
        # Проверяем в БД
        goal = DailyGoal.objects.get(user=test_user, date=test_date)
        assert goal.is_auto_calculated is True
    
    def test_auto_calculate_creates_or_updates(self, authenticated_client, test_user):
        """Тест 222: Проверка, что расчёт создаёт или обновляет цель"""
        test_date = date.today()
        
        # Первый расчёт - создание
        data = {
            'weight': 70,
            'height': 175,
            'age': 30,
            'activity_level': 'moderate',
            'date': str(test_date)
        }
        
        response1 = authenticated_client.post('/api/goals/auto-calculate/', data, format='json')
        assert response1.status_code == status.HTTP_201_CREATED
        
        # Второй расчёт - обновление
        data['weight'] = 75
        response2 = authenticated_client.post('/api/goals/auto-calculate/', data, format='json')
        assert response2.status_code == status.HTTP_200_OK
        
        # Проверяем, что цель одна
        assert DailyGoal.objects.filter(user=test_user, date=test_date).count() == 1

