from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Кастомная модель пользователя"""
    email = models.EmailField(unique=True, verbose_name='Email')
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        db_table = 'users'


class Profile(models.Model):
    """Профиль пользователя с дополнительными данными"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Пользователь'
    )
    first_name = models.CharField(max_length=150, blank=True, verbose_name='Имя')
    last_name = models.CharField(max_length=150, blank=True, verbose_name='Фамилия')
    age = models.PositiveIntegerField(null=True, blank=True, verbose_name='Возраст')
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Вес (кг)'
    )
    height = models.PositiveIntegerField(null=True, blank=True, verbose_name='Рост (см)')
    activity_level = models.CharField(
        max_length=20,
        choices=[
            ('sedentary', 'Малоподвижный'),
            ('light', 'Лёгкая активность'),
            ('moderate', 'Умеренная активность'),
            ('active', 'Высокая активность'),
            ('very_active', 'Очень высокая активность'),
        ],
        default='sedentary',
        verbose_name='Уровень активности'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'
        db_table = 'profiles'
    
    def __str__(self):
        return f'Профиль {self.user.username}'
