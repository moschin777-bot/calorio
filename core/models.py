from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator

User = get_user_model()


class DailyGoal(models.Model):
    """Модель целей КБЖУ на день"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='daily_goals',
        verbose_name='Пользователь'
    )
    date = models.DateField(verbose_name='Дата')
    calories = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Калории (ккал)'
    )
    proteins = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Белки (г)'
    )
    fats = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Жиры (г)'
    )
    carbohydrates = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Углеводы (г)'
    )
    is_auto_calculated = models.BooleanField(
        default=False,
        verbose_name='Автоматически рассчитано'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Цель на день'
        verbose_name_plural = 'Цели на день'
        db_table = 'daily_goals'
        unique_together = ['user', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['-date']),
        ]
    
    def __str__(self):
        return f'Цель {self.user.username} на {self.date}'


class Meal(models.Model):
    """Модель приёма пищи"""
    MEAL_TYPE_CHOICES = [
        ('breakfast', 'Завтрак'),
        ('lunch', 'Обед'),
        ('dinner', 'Ужин'),
        ('snack', 'Перекус'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='meals',
        verbose_name='Пользователь'
    )
    date = models.DateField(verbose_name='Дата')
    meal_type = models.CharField(
        max_length=20,
        choices=MEAL_TYPE_CHOICES,
        verbose_name='Тип приёма пищи'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Приём пищи'
        verbose_name_plural = 'Приёмы пищи'
        db_table = 'meals'
        ordering = ['-date', 'meal_type']
        indexes = [
            models.Index(fields=['user', 'date', 'meal_type']),
            models.Index(fields=['-date']),
        ]
    
    def __str__(self):
        return f'{self.get_meal_type_display()} {self.user.username} на {self.date}'


class Dish(models.Model):
    """Модель блюда с КБЖУ"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='dishes',
        verbose_name='Пользователь',
        null=True,
        blank=True
    )
    meal = models.ForeignKey(
        Meal,
        on_delete=models.CASCADE,
        related_name='dishes',
        verbose_name='Приём пищи',
        null=True,
        blank=True
    )
    name = models.CharField(max_length=255, verbose_name='Название блюда')
    weight = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Масса (г)'
    )
    calories = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        verbose_name='Калории (ккал)'
    )
    proteins = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Белки (г)'
    )
    fats = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Жиры (г)'
    )
    carbohydrates = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Углеводы (г)'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Блюдо'
        verbose_name_plural = 'Блюда'
        db_table = 'dishes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['meal']),
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        user_info = f' ({self.user.username})' if self.user else ''
        return f'{self.name}{user_info}'


class DishImage(models.Model):
    """Модель изображения блюда для распознавания"""
    dish = models.ForeignKey(
        Dish,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='Блюдо'
    )
    image = models.ImageField(
        upload_to='dish_images/',
        verbose_name='Изображение'
    )
    is_recognized = models.BooleanField(
        default=False,
        verbose_name='Распознано'
    )
    recognition_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Данные распознавания'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    
    class Meta:
        verbose_name = 'Изображение блюда'
        verbose_name_plural = 'Изображения блюд'
        db_table = 'dish_images'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'Изображение для {self.dish.name}'
