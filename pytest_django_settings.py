"""
Настройки Django для pytest
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'calorio_api.settings')
os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-testing-only')
os.environ.setdefault('DEBUG', 'True')
os.environ.setdefault('ALLOWED_HOSTS', 'localhost,127.0.0.1')

