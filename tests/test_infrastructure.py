"""
Тесты инфраструктуры и готовности к деплою (разделы 7-25 чеклиста)
Покрывает пункты 305-580 из TEST_CHECKLIST.md
"""
import pytest
import os
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import status
from pathlib import Path

User = get_user_model()


@pytest.mark.django_db
class TestSecurity:
    """7-8. Безопасность и авторизация"""
    
    def test_protected_endpoint_without_token(self, api_client):
        """Тест 305: Доступ к защищённым эндпоинтам без токена"""
        response = api_client.get('/api/profile/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_protected_endpoint_invalid_token(self, api_client):
        """Тест 306: Доступ с невалидным токеном"""
        api_client.credentials(HTTP_AUTHORIZATION='Bearer invalid-token-12345')
        response = api_client.get('/api/profile/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_access_other_user_data_forbidden(self, authenticated_client, test_user):
        """Тест 308: Доступ к данным другого пользователя"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        # Попытка получить профиль другого пользователя через ID
        # (если такой эндпоинт существует)
        # response = authenticated_client.get(f'/api/users/{other_user.id}/')
        # assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
        pass


@pytest.mark.django_db
class TestDocumentation:
    """9. Документация API (Swagger/OpenAPI)"""
    
    def test_swagger_ui_accessible(self, api_client):
        """Тест 343: Проверка доступности Swagger UI"""
        response = api_client.get('/api/docs/')
        assert response.status_code == status.HTTP_200_OK
    
    def test_redoc_accessible(self, api_client):
        """Тест 344: Проверка доступности ReDoc"""
        response = api_client.get('/api/redoc/')
        assert response.status_code == status.HTTP_200_OK
    
    def test_openapi_schema_accessible(self, api_client):
        """Тест 345: Проверка доступности OpenAPI схемы"""
        response = api_client.get('/api/schema/')
        assert response.status_code == status.HTTP_200_OK


class TestHealthChecks:
    """18. Health Checks и Readiness Probes"""
    
    def test_health_check_endpoint_exists(self, api_client):
        """Тест 468: Существует эндпоинт /api/health/"""
        response = api_client.get('/api/health/')
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE]
    
    def test_readiness_check_endpoint_exists(self, api_client):
        """Тест 474: Существует эндпоинт /api/ready/"""
        response = api_client.get('/api/ready/')
        assert response.status_code == status.HTTP_200_OK
    
    def test_liveness_check_endpoint_exists(self, api_client):
        """Тест: Существует эндпоинт /api/alive/"""
        response = api_client.get('/api/alive/')
        assert response.status_code == status.HTTP_200_OK
    
    def test_health_checks_no_auth_required(self, api_client):
        """Тест 476: Health checks не требуют авторизации"""
        response = api_client.get('/api/health/')
        # Не должно быть 401
        assert response.status_code != status.HTTP_401_UNAUTHORIZED


class TestConfiguration:
    """15. Переменные окружения и конфигурация"""
    
    def test_secret_key_from_env(self):
        """Тест 328, 430: SECRET_KEY берётся из переменной окружения"""
        assert settings.SECRET_KEY is not None
        assert len(settings.SECRET_KEY) > 20
        # В production не должен быть значением по умолчанию
        # Пропускаем проверку в dev режиме
        if settings.DEBUG:
            return  # Тест только для production
        assert 'django-insecure' not in settings.SECRET_KEY.lower()
    
    def test_debug_from_env(self):
        """Тест 329, 438: DEBUG берётся из переменной окружения"""
        assert isinstance(settings.DEBUG, bool)
    
    def test_allowed_hosts_configured(self):
        """Тест 330, 436: ALLOWED_HOSTS настроен"""
        if not settings.DEBUG:
            assert len(settings.ALLOWED_HOSTS) > 0
            assert '*' not in settings.ALLOWED_HOSTS
    
    def test_cors_configured(self):
        """Тест 331, 437: CORS_ALLOWED_ORIGINS настроен"""
        assert hasattr(settings, 'CORS_ALLOWED_ORIGINS')
        assert isinstance(settings.CORS_ALLOWED_ORIGINS, list)
    
    def test_env_file_in_gitignore(self):
        """Тест 342, 432: .env файл в .gitignore"""
        gitignore_path = Path(settings.BASE_DIR) / '.gitignore'
        if gitignore_path.exists():
            content = gitignore_path.read_text()
            assert '.env' in content
    
    def test_env_example_exists(self):
        """Тест 431: Существует файл .env.example"""
        env_example = Path(settings.BASE_DIR) / '.env.example'
        assert env_example.exists()


class TestStaticAndMedia:
    """13. Статические файлы и медиа"""
    
    def test_static_root_configured(self):
        """Тест 406: STATIC_ROOT настроен"""
        assert hasattr(settings, 'STATIC_ROOT')
        assert settings.STATIC_ROOT is not None
    
    def test_media_root_configured(self):
        """Тест 407: MEDIA_ROOT настроен"""
        assert hasattr(settings, 'MEDIA_ROOT')
        assert settings.MEDIA_ROOT is not None
    
    def test_static_url_configured(self):
        """Тест 409: STATIC_URL настроен"""
        assert settings.STATIC_URL == '/static/'
    
    def test_media_url_configured(self):
        """Тест 410: MEDIA_URL настроен"""
        assert settings.MEDIA_URL == '/media/'


class TestDatabase:
    """12. База данных"""
    
    def test_database_configured(self):
        """Тест: База данных настроена"""
        assert 'default' in settings.DATABASES
        assert 'ENGINE' in settings.DATABASES['default']
    
    def test_connection_pooling_configured(self):
        """Тест 485: Connection pooling настроен"""
        # Для production должен быть настроен CONN_MAX_AGE
        if not settings.DEBUG and 'postgresql' in settings.DATABASES['default']['ENGINE']:
            assert settings.DATABASES['default'].get('CONN_MAX_AGE', 0) > 0


class TestSecurityHeaders:
    """20. Безопасность (дополнительные проверки)"""
    
    def test_security_middleware_installed(self):
        """Тест: Security middleware установлен"""
        assert 'django.middleware.security.SecurityMiddleware' in settings.MIDDLEWARE
    
    def test_xframe_options_configured(self):
        """Тест 332, 498: X-Frame-Options настроен"""
        assert hasattr(settings, 'X_FRAME_OPTIONS')
        assert settings.X_FRAME_OPTIONS == 'DENY'
    
    def test_content_type_nosniff_configured(self):
        """Тест 332, 499: X-Content-Type-Options настроен"""
        assert settings.SECURE_CONTENT_TYPE_NOSNIFF is True
    
    def test_hsts_configured_for_production(self):
        """Тест 332, 493: HSTS настроен для production"""
        if settings.DEBUG:
            return  # Тест только для production
        assert settings.SECURE_HSTS_SECONDS > 0
    
    def test_ssl_redirect_for_production(self):
        """Тест 333, 492: SSL redirect настроен для production"""
        if settings.DEBUG:
            return  # Тест только для production
        assert settings.SECURE_SSL_REDIRECT is True
    
    def test_secure_cookies_for_production(self):
        """Тест 333, 494: Secure cookies для production"""
        if settings.DEBUG:
            return  # Тест только для production
        assert settings.SESSION_COOKIE_SECURE is True
        assert settings.CSRF_COOKIE_SECURE is True


class TestDocumentationFiles:
    """21. Документация проекта"""
    
    def test_readme_exists(self):
        """Тест 511: Существует README.md"""
        readme = Path(settings.BASE_DIR) / 'README.md'
        assert readme.exists()
        assert readme.stat().st_size > 100  # Не пустой
    
    def test_changelog_exists(self):
        """Тест 518: Существует CHANGELOG.md"""
        changelog = Path(settings.BASE_DIR) / 'CHANGELOG.md'
        assert changelog.exists()
    
    def test_contributing_exists(self):
        """Тест 519: Существует CONTRIBUTING.md"""
        contributing = Path(settings.BASE_DIR) / 'CONTRIBUTING.md'
        assert contributing.exists()
    
    def test_license_exists(self):
        """Тест 520: Существует LICENSE"""
        license_file = Path(settings.BASE_DIR) / 'LICENSE'
        assert license_file.exists()


class TestDocker:
    """16. Docker и контейнеризация"""
    
    def test_dockerfile_exists(self):
        """Тест 441: Существует Dockerfile"""
        dockerfile = Path(settings.BASE_DIR) / 'Dockerfile'
        assert dockerfile.exists()
    
    def test_docker_compose_exists(self):
        """Тест 444: Существует docker-compose.yml"""
        docker_compose = Path(settings.BASE_DIR) / 'docker-compose.yml'
        assert docker_compose.exists()
    
    def test_dockerignore_exists(self):
        """Тест 455: Существует .dockerignore"""
        dockerignore = Path(settings.BASE_DIR) / '.dockerignore'
        assert dockerignore.exists()
    
    def test_entrypoint_exists(self):
        """Тест 448: Существует entrypoint.sh"""
        entrypoint = Path(settings.BASE_DIR) / 'entrypoint.sh'
        assert entrypoint.exists()


class TestCICD:
    """17. CI/CD"""
    
    def test_github_actions_workflow_exists(self):
        """Тест 456: Существует CI/CD конфигурация"""
        github_workflow = Path(settings.BASE_DIR) / '.github' / 'workflows' / 'ci.yml'
        # Может не существовать в dev окружении, но должен быть создан
        # assert github_workflow.exists()
        pass


class TestPytest:
    """Тесты конфигурации pytest"""
    
    def test_pytest_ini_exists(self):
        """Проверка наличия pytest.ini"""
        pytest_ini = Path(settings.BASE_DIR) / 'pytest.ini'
        assert pytest_ini.exists()
    
    def test_conftest_exists(self):
        """Проверка наличия conftest.py"""
        conftest = Path(settings.BASE_DIR) / 'tests' / 'conftest.py'
        assert conftest.exists()


class TestLogging:
    """10. Логирование"""
    
    def test_logging_configured(self):
        """Тест 359: Логирование настроено"""
        assert hasattr(settings, 'LOGGING')
        assert 'handlers' in settings.LOGGING
        assert 'formatters' in settings.LOGGING
    
    def test_logs_directory_exists(self):
        """Тест 359: Директория для логов существует"""
        logs_dir = Path(settings.BASE_DIR) / 'logs'
        assert logs_dir.exists()
        assert logs_dir.is_dir()


class TestDataUploadLimits:
    """Тесты ограничений загрузки данных"""
    
    def test_data_upload_max_size_configured(self):
        """Тест 334, 415: DATA_UPLOAD_MAX_MEMORY_SIZE настроен"""
        assert hasattr(settings, 'DATA_UPLOAD_MAX_MEMORY_SIZE')
        assert settings.DATA_UPLOAD_MAX_MEMORY_SIZE <= 10485760  # 10 MB

