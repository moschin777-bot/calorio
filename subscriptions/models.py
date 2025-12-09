"""
Модели для системы подписок
"""
from django.db import models
from django.conf import settings
from datetime import timedelta
from django.utils import timezone


class SubscriptionPlan(models.Model):
    """Тарифный план подписки"""
    
    name = models.CharField(
        max_length=100,
        verbose_name='Название плана',
        help_text='Например: Basic, Premium, Pro'
    )
    price_monthly = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Цена за месяц',
        help_text='Цена в рублях'
    )
    price_yearly = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Цена за год',
        help_text='Цена в рублях (обычно со скидкой)'
    )
    features = models.JSONField(
        default=list,
        verbose_name='Возможности плана',
        help_text='Список возможностей в формате JSON'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен',
        help_text='Доступен ли план для покупки'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Тарифный план'
        verbose_name_plural = 'Тарифные планы'
        ordering = ['price_monthly']
    
    def __str__(self):
        return f"{self.name} - {self.price_monthly}₽/мес"


class Subscription(models.Model):
    """Подписка пользователя"""
    
    STATUS_CHOICES = [
        ('active', 'Активна'),
        ('expired', 'Истекла'),
        ('cancelled', 'Отменена'),
    ]
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscription',
        verbose_name='Пользователь'
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subscriptions',
        verbose_name='Тарифный план'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='expired',
        verbose_name='Статус'
    )
    start_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата начала'
    )
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата окончания'
    )
    auto_renew = models.BooleanField(
        default=True,
        verbose_name='Автопродление',
        help_text='Автоматически продлевать подписку'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Подписка {self.user.email} - {self.status}"
    
    def activate(self, duration_days):
        """Активировать подписку на указанное количество дней"""
        self.status = 'active'
        self.start_date = timezone.now()
        self.end_date = self.start_date + timedelta(days=duration_days)
        self.save()
    
    def is_active(self):
        """Проверка активности подписки"""
        if self.status != 'active':
            return False
        if not self.end_date:
            return False
        return timezone.now() < self.end_date
    
    def days_remaining(self):
        """Количество дней до окончания"""
        if not self.is_active():
            return 0
        delta = self.end_date - timezone.now()
        return max(0, delta.days)


class Payment(models.Model):
    """Платёж за подписку"""
    
    PAYMENT_TYPE_CHOICES = [
        ('monthly', 'Месячная'),
        ('yearly', 'Годовая'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Ожидает оплаты'),
        ('completed', 'Оплачен'),
        ('failed', 'Ошибка'),
        ('refunded', 'Возвращён'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='Пользователь'
    )
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='Подписка'
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        related_name='payments',
        verbose_name='Тарифный план'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Сумма',
        help_text='Сумма в рублях'
    )
    payment_type = models.CharField(
        max_length=20,
        choices=PAYMENT_TYPE_CHOICES,
        verbose_name='Тип оплаты'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус'
    )
    transaction_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        unique=True,
        verbose_name='ID транзакции',
        help_text='ID транзакции от платёжного провайдера'
    )
    payment_url = models.URLField(
        null=True,
        blank=True,
        verbose_name='URL для оплаты',
        help_text='Ссылка на страницу оплаты'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Платёж'
        verbose_name_plural = 'Платежи'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Платёж {self.user.email} - {self.amount}₽ ({self.status})"
    
    def complete(self):
        """Отметить платёж как завершённый и активировать подписку"""
        self.status = 'completed'
        self.save()
        
        # Активируем подписку
        if self.subscription:
            duration_days = 30 if self.payment_type == 'monthly' else 365
            self.subscription.activate(duration_days)

