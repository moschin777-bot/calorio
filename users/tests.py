from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Profile

User = get_user_model()


class AuthenticationTests(TestCase):
    """Тесты для аутентификации и авторизации"""
    
    def setUp(self):
        """Настройка тестового окружения"""
        self.client = APIClient()
        self.register_url = '/api/auth/register/'
        self.login_url = '/api/auth/login/'
        self.logout_url = '/api/auth/logout/'
        self.token_refresh_url = '/api/auth/token/refresh/'
        
        # Тестовые данные для регистрации
        self.valid_registration_data = {
            'first_name': 'Иван',
            'email': 'ivan@example.com',
            'password': 'testpass123'
        }
        
        # Тестовые данные для входа
        self.valid_login_data = {
            'email': 'ivan@example.com',
            'password': 'testpass123'
        }
    
    def test_user_registration_success(self):
        """Тест успешной регистрации пользователя"""
        response = self.client.post(self.register_url, self.valid_registration_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        self.assertEqual(response.data['user']['email'], 'ivan@example.com')
        self.assertEqual(response.data['user']['first_name'], 'Иван')
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        
        # Проверяем, что пользователь создан в БД
        self.assertTrue(User.objects.filter(email='ivan@example.com').exists())
        
        # Проверяем, что профиль создан
        user = User.objects.get(email='ivan@example.com')
        self.assertTrue(Profile.objects.filter(user=user).exists())
        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.first_name, 'Иван')
    
    def test_user_registration_duplicate_email(self):
        """Тест регистрации с уже существующим email"""
        # Создаём первого пользователя
        self.client.post(self.register_url, self.valid_registration_data, format='json')
        
        # Пытаемся создать второго с тем же email
        response = self.client.post(self.register_url, self.valid_registration_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
    
    def test_user_registration_short_password(self):
        """Тест регистрации с коротким паролем"""
        data = self.valid_registration_data.copy()
        data['password'] = 'short'
        
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
    
    def test_user_registration_invalid_email(self):
        """Тест регистрации с невалидным email"""
        data = self.valid_registration_data.copy()
        data['email'] = 'invalid-email'
        
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
    
    def test_user_registration_empty_first_name(self):
        """Тест регистрации с пустым именем"""
        data = self.valid_registration_data.copy()
        data['first_name'] = ''
        
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('first_name', response.data)
    
    def test_user_registration_long_first_name(self):
        """Тест регистрации с слишком длинным именем"""
        data = self.valid_registration_data.copy()
        data['first_name'] = 'a' * 151  # Больше 150 символов
        
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('first_name', response.data)
    
    def test_user_login_success(self):
        """Тест успешного входа"""
        # Сначала регистрируем пользователя
        self.client.post(self.register_url, self.valid_registration_data, format='json')
        
        # Теперь входим
        response = self.client.post(self.login_url, self.valid_login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        self.assertEqual(response.data['user']['email'], 'ivan@example.com')
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
    
    def test_user_login_wrong_password(self):
        """Тест входа с неверным паролем"""
        # Регистрируем пользователя
        self.client.post(self.register_url, self.valid_registration_data, format='json')
        
        # Пытаемся войти с неверным паролем
        data = self.valid_login_data.copy()
        data['password'] = 'wrongpassword'
        
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)
    
    def test_user_login_nonexistent_email(self):
        """Тест входа с несуществующим email"""
        response = self.client.post(self.login_url, self.valid_login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)
    
    def test_user_login_invalid_email(self):
        """Тест входа с невалидным email"""
        data = self.valid_login_data.copy()
        data['email'] = 'invalid-email'
        
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
    
    def test_token_refresh(self):
        """Тест обновления токена"""
        # Регистрируем пользователя
        register_response = self.client.post(self.register_url, self.valid_registration_data, format='json')
        refresh_token = register_response.data['tokens']['refresh']
        
        # Обновляем токен
        response = self.client.post(self.token_refresh_url, {'refresh': refresh_token}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_user_logout_success(self):
        """Тест успешного выхода"""
        # Регистрируем и входим
        register_response = self.client.post(self.register_url, self.valid_registration_data, format='json')
        access_token = register_response.data['tokens']['access']
        refresh_token = register_response.data['tokens']['refresh']
        
        # Устанавливаем токен для аутентификации
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Выходим
        response = self.client.post(self.logout_url, {'refresh': refresh_token}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('detail', response.data)
        self.assertEqual(response.data['detail'], 'Успешный выход из системы.')
    
    def test_user_logout_without_token(self):
        """Тест выхода без токена"""
        # Регистрируем и входим
        register_response = self.client.post(self.register_url, self.valid_registration_data, format='json')
        access_token = register_response.data['tokens']['access']
        
        # Устанавливаем токен для аутентификации
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Пытаемся выйти без refresh токена
        response = self.client.post(self.logout_url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_user_logout_unauthenticated(self):
        """Тест выхода без аутентификации"""
        response = self.client.post(self.logout_url, {'refresh': 'some-token'}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ProfileTests(TestCase):
    """Тесты для профиля пользователя"""
    
    def setUp(self):
        """Настройка тестового окружения"""
        self.client = APIClient()
        self.register_url = '/api/auth/register/'
        self.profile_url = '/api/profile/'
        self.password_change_url = '/api/profile/change-password/'
        
        # Регистрируем тестового пользователя
        registration_data = {
            'first_name': 'Иван',
            'email': 'ivan@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(self.register_url, registration_data, format='json')
        self.access_token = response.data['tokens']['access']
        self.user_id = response.data['user']['id']
        
        # Устанавливаем токен для аутентификации
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_get_profile(self):
        """Тест получения профиля"""
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.user_id)
        self.assertEqual(response.data['email'], 'ivan@example.com')
        self.assertEqual(response.data['first_name'], 'Иван')
    
    def test_update_profile_first_name(self):
        """Тест обновления имени"""
        data = {'first_name': 'Пётр'}
        response = self.client.patch(self.profile_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Пётр')
    
    def test_update_profile_email(self):
        """Тест обновления email"""
        data = {'email': 'newemail@example.com'}
        response = self.client.patch(self.profile_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'newemail@example.com')
    
    def test_update_profile_both_fields(self):
        """Тест обновления имени и email одновременно"""
        data = {
            'first_name': 'Пётр',
            'email': 'petr@example.com'
        }
        response = self.client.patch(self.profile_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Пётр')
        self.assertEqual(response.data['email'], 'petr@example.com')
    
    def test_update_profile_duplicate_email(self):
        """Тест обновления email на уже существующий"""
        # Создаём второго пользователя
        self.client.credentials()  # Убираем аутентификацию
        self.client.post(self.register_url, {
            'first_name': 'Мария',
            'email': 'maria@example.com',
            'password': 'testpass123'
        }, format='json')
        
        # Возвращаем аутентификацию первого пользователя
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        # Пытаемся изменить email на уже существующий
        data = {'email': 'maria@example.com'}
        response = self.client.patch(self.profile_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
    
    def test_change_password_success(self):
        """Тест успешной смены пароля"""
        data = {
            'old_password': 'testpass123',
            'new_password': 'newpass123'
        }
        response = self.client.post(self.password_change_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('detail', response.data)
        
        # Проверяем, что можем войти с новым паролем
        self.client.credentials()  # Убираем аутентификацию
        login_response = self.client.post('/api/auth/login/', {
            'email': 'ivan@example.com',
            'password': 'newpass123'
        }, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
    
    def test_change_password_wrong_old_password(self):
        """Тест смены пароля с неверным старым паролем"""
        data = {
            'old_password': 'wrongpassword',
            'new_password': 'newpass123'
        }
        response = self.client.post(self.password_change_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('old_password', response.data)
    
    def test_change_password_short_new_password(self):
        """Тест смены пароля на слишком короткий"""
        data = {
            'old_password': 'testpass123',
            'new_password': 'short'
        }
        response = self.client.post(self.password_change_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new_password', response.data)
    
    def test_change_password_same_as_old(self):
        """Тест смены пароля на такой же"""
        data = {
            'old_password': 'testpass123',
            'new_password': 'testpass123'
        }
        response = self.client.post(self.password_change_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new_password', response.data)
    
    def test_get_profile_unauthenticated(self):
        """Тест получения профиля без аутентификации"""
        self.client.credentials()  # Убираем аутентификацию
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
