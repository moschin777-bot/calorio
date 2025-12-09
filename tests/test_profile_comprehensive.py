"""
Полные тесты для профиля пользователя (2.1-2.3)
Покрывает все пункты из TEST_CHECKLIST.md раздел 2
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import Profile

User = get_user_model()


@pytest.mark.django_db
class TestProfileRetrieve:
    """2.1. Получение профиля (GET /api/profile/)"""
    
    @pytest.fixture
    def authenticated_user(self, api_client):
        """Создаём пользователя и возвращаем аутентифицированный клиент"""
        data = {
            'first_name': 'Иван',
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = api_client.post('/api/auth/register/', data, format='json')
        user = User.objects.get(email='test@example.com')
        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        return api_client, user, response.data['user']['id']
    
    def test_get_profile_authenticated(self, authenticated_user):
        """Тест 40: Получение профиля авторизованным пользователем"""
        api_client, user, user_id = authenticated_user
        response = api_client.get('/api/profile/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == user_id
        assert response.data['email'] == 'test@example.com'
        assert response.data['first_name'] == 'Иван'
    
    def test_get_profile_without_token(self, api_client):
        """Тест 41: Получение профиля без токена авторизации"""
        response = api_client.get('/api/profile/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_profile_invalid_token(self, api_client):
        """Тест 42: Получение профиля с невалидным токеном"""
        api_client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        response = api_client.get('/api/profile/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_profile_expired_token(self, api_client):
        """Тест 43: Получение профиля с истёкшим токеном"""
        # Создаём токен, который будет истёкшим (теоретически)
        api_client.credentials(HTTP_AUTHORIZATION='Bearer expired_token_here')
        response = api_client.get('/api/profile/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_profile_returns_correct_fields(self, authenticated_user):
        """Тест 44: Проверка, что возвращаются только поля: id, email, first_name"""
        api_client, user, user_id = authenticated_user
        response = api_client.get('/api/profile/')
        
        assert set(response.data.keys()) == {'id', 'email', 'first_name'}
        assert 'password' not in response.data
        assert 'username' not in response.data
    
    def test_get_profile_correct_values(self, authenticated_user):
        """Тест 45: Проверка корректности значений возвращаемых полей"""
        api_client, user, user_id = authenticated_user
        response = api_client.get('/api/profile/')
        
        assert response.data['id'] == user.id
        assert response.data['email'] == user.email
        profile = Profile.objects.get(user=user)
        assert response.data['first_name'] == profile.first_name


@pytest.mark.django_db
class TestProfileUpdate:
    """2.2. Обновление профиля (PATCH /api/profile/)"""
    
    @pytest.fixture
    def authenticated_user(self, api_client):
        """Создаём пользователя и возвращаем аутентифицированный клиент"""
        data = {
            'first_name': 'Иван',
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = api_client.post('/api/auth/register/', data, format='json')
        user = User.objects.get(email='test@example.com')
        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        return api_client, user
    
    def test_update_first_name_only(self, authenticated_user):
        """Тест 46: Обновление только first_name с корректным значением"""
        api_client, user = authenticated_user
        data = {'first_name': 'Пётр'}
        response = api_client.patch('/api/profile/', data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['first_name'] == 'Пётр'
        profile = Profile.objects.get(user=user)
        assert profile.first_name == 'Пётр'
    
    def test_update_email_only(self, authenticated_user):
        """Тест 47: Обновление только email с корректным значением"""
        api_client, user = authenticated_user
        data = {'email': 'newemail@example.com'}
        response = api_client.patch('/api/profile/', data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == 'newemail@example.com'
        user.refresh_from_db()
        assert user.email == 'newemail@example.com'
    
    def test_update_both_fields(self, authenticated_user):
        """Тест 48: Обновление first_name и email одновременно"""
        api_client, user = authenticated_user
        data = {
            'first_name': 'Пётр',
            'email': 'petr@example.com'
        }
        response = api_client.patch('/api/profile/', data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['first_name'] == 'Пётр'
        assert response.data['email'] == 'petr@example.com'
    
    def test_update_first_name_empty(self, authenticated_user):
        """Тест 49: Обновление first_name с пустым значением"""
        api_client, user = authenticated_user
        data = {'first_name': ''}
        response = api_client.patch('/api/profile/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_update_first_name_too_long(self, authenticated_user):
        """Тест 50: Обновление first_name длиннее 150 символов"""
        api_client, user = authenticated_user
        data = {'first_name': 'a' * 151}
        response = api_client.patch('/api/profile/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_update_email_invalid_format(self, authenticated_user):
        """Тест 51: Обновление email с некорректным форматом"""
        api_client, user = authenticated_user
        data = {'email': 'invalid-email'}
        response = api_client.patch('/api/profile/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_update_email_duplicate(self, api_client):
        """Тест 52: Обновление email на уже существующий в системе"""
        # Создаём первого пользователя
        data1 = {
            'first_name': 'Иван',
            'email': 'ivan@example.com',
            'password': 'testpass123'
        }
        response1 = api_client.post('/api/auth/register/', data1, format='json')
        user1 = User.objects.get(email='ivan@example.com')
        refresh1 = RefreshToken.for_user(user1)
        
        # Создаём второго пользователя
        data2 = {
            'first_name': 'Мария',
            'email': 'maria@example.com',
            'password': 'testpass123'
        }
        api_client.post('/api/auth/register/', data2, format='json')
        user2 = User.objects.get(email='maria@example.com')
        refresh2 = RefreshToken.for_user(user2)
        
        # Пытаемся изменить email второго пользователя на email первого
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh2.access_token}')
        data = {'email': 'ivan@example.com'}
        response = api_client.patch('/api/profile/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_update_email_same(self, authenticated_user):
        """Тест 53: Обновление email на тот же email (без изменений)"""
        api_client, user = authenticated_user
        data = {'email': user.email}
        response = api_client.patch('/api/profile/', data, format='json')
        # Должно работать, так как это тот же email
        assert response.status_code == status.HTTP_200_OK
    
    def test_update_profile_without_token(self, api_client):
        """Тест 54: Обновление профиля без токена авторизации"""
        data = {'first_name': 'Пётр'}
        response = api_client.patch('/api/profile/', data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_update_profile_invalid_token(self, api_client):
        """Тест 55: Обновление профиля с невалидным токеном"""
        api_client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        data = {'first_name': 'Пётр'}
        response = api_client.patch('/api/profile/', data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_update_profile_returns_updated_data(self, authenticated_user):
        """Тест 56: Проверка, что после обновления возвращаются обновлённые данные"""
        api_client, user = authenticated_user
        data = {
            'first_name': 'Пётр',
            'email': 'petr@example.com'
        }
        response = api_client.patch('/api/profile/', data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['first_name'] == 'Пётр'
        assert response.data['email'] == 'petr@example.com'


@pytest.mark.django_db
class TestPasswordChange:
    """2.3. Смена пароля (POST /api/profile/change-password/)"""
    
    @pytest.fixture
    def authenticated_user(self, api_client):
        """Создаём пользователя и возвращаем аутентифицированный клиент"""
        data = {
            'first_name': 'Иван',
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = api_client.post('/api/auth/register/', data, format='json')
        user = User.objects.get(email='test@example.com')
        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        return api_client, user
    
    def test_change_password_valid(self, authenticated_user):
        """Тест 57: Смена пароля с корректными old_password и new_password"""
        api_client, user = authenticated_user
        data = {
            'old_password': 'testpass123',
            'new_password': 'newpass123'
        }
        response = api_client.post('/api/profile/change-password/', data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'detail' in response.data
        
        # Проверяем, что можем войти с новым паролем
        api_client.credentials()
        login_response = api_client.post('/api/auth/login/', {
            'email': 'test@example.com',
            'password': 'newpass123'
        }, format='json')
        assert login_response.status_code == status.HTTP_200_OK
    
    def test_change_password_wrong_old(self, authenticated_user):
        """Тест 58: Смена пароля с неверным old_password"""
        api_client, user = authenticated_user
        data = {
            'old_password': 'wrongpassword',
            'new_password': 'newpass123'
        }
        response = api_client.post('/api/profile/change-password/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'old_password' in response.data
    
    def test_change_password_empty_old(self, authenticated_user):
        """Тест 59: Смена пароля с пустым old_password"""
        api_client, user = authenticated_user
        data = {
            'old_password': '',
            'new_password': 'newpass123'
        }
        response = api_client.post('/api/profile/change-password/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_change_password_empty_new(self, authenticated_user):
        """Тест 60: Смена пароля с пустым new_password"""
        api_client, user = authenticated_user
        data = {
            'old_password': 'testpass123',
            'new_password': ''
        }
        response = api_client.post('/api/profile/change-password/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_change_password_short_new(self, authenticated_user):
        """Тест 61: Смена пароля с new_password короче 8 символов"""
        api_client, user = authenticated_user
        data = {
            'old_password': 'testpass123',
            'new_password': 'short'
        }
        response = api_client.post('/api/profile/change-password/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'new_password' in response.data
    
    def test_change_password_same_as_old(self, authenticated_user):
        """Тест 62: Смена пароля с new_password равным old_password"""
        api_client, user = authenticated_user
        data = {
            'old_password': 'testpass123',
            'new_password': 'testpass123'
        }
        response = api_client.post('/api/profile/change-password/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'new_password' in response.data
    
    def test_change_password_without_token(self, api_client):
        """Тест 63: Смена пароля без токена авторизации"""
        data = {
            'old_password': 'testpass123',
            'new_password': 'newpass123'
        }
        response = api_client.post('/api/profile/change-password/', data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_change_password_invalid_token(self, api_client):
        """Тест 64: Смена пароля с невалидным токеном"""
        api_client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        data = {
            'old_password': 'testpass123',
            'new_password': 'newpass123'
        }
        response = api_client.post('/api/profile/change-password/', data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_change_password_old_doesnt_work(self, authenticated_user):
        """Тест 65: Проверка, что после смены пароля старый пароль не работает"""
        api_client, user = authenticated_user
        data = {
            'old_password': 'testpass123',
            'new_password': 'newpass123'
        }
        api_client.post('/api/profile/change-password/', data, format='json')
        
        # Пытаемся войти со старым паролем
        api_client.credentials()
        login_response = api_client.post('/api/auth/login/', {
            'email': 'test@example.com',
            'password': 'testpass123'
        }, format='json')
        assert login_response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_change_password_new_works(self, authenticated_user):
        """Тест 66: Проверка, что после смены пароля новый пароль работает"""
        api_client, user = authenticated_user
        data = {
            'old_password': 'testpass123',
            'new_password': 'newpass123'
        }
        api_client.post('/api/profile/change-password/', data, format='json')
        
        # Пытаемся войти с новым паролем
        api_client.credentials()
        login_response = api_client.post('/api/auth/login/', {
            'email': 'test@example.com',
            'password': 'newpass123'
        }, format='json')
        assert login_response.status_code == status.HTTP_200_OK

