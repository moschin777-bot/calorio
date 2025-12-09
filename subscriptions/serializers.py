from rest_framework import serializers
from .models import Subscription, SubscriptionPlan, Payment
from datetime import datetime, timezone


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Сериализатор для тарифного плана"""
    
    class Meta:
        model = SubscriptionPlan
        fields = ('id', 'name', 'price_monthly', 'price_yearly', 'features', 'is_active')
        read_only_fields = ('id',)


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для подписки"""
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    days_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = Subscription
        fields = (
            'id', 'plan_name', 'status', 'days_remaining', 
            'end_date', 'auto_renew', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def get_days_remaining(self, obj):
        """Расчёт остатка дней до окончания подписки"""
        if obj.status != 'active' or not obj.end_date:
            return None
        
        now = datetime.now(timezone.utc)
        if obj.end_date.tzinfo is None:
            # Если end_date без timezone, добавляем UTC
            from django.utils import timezone as django_tz
            end_date = django_tz.make_aware(obj.end_date, timezone.utc)
        else:
            end_date = obj.end_date
        
        delta = end_date - now
        days = delta.days
        
        return days if days >= 0 else 0


class PaymentSerializer(serializers.ModelSerializer):
    """Сериализатор для платежа"""
    plan_name = serializers.CharField(source='subscription.plan.name', read_only=True)
    
    class Meta:
        model = Payment
        fields = (
            'id', 'plan_name', 'amount', 'payment_type', 
            'status', 'created_at'
        )
        read_only_fields = ('id', 'created_at')


class CreatePaymentSerializer(serializers.Serializer):
    """Сериализатор для создания платежа"""
    plan_id = serializers.IntegerField(required=False)
    
    def validate_plan_id(self, value):
        """Валидация ID тарифного плана"""
        if value:
            try:
                plan = SubscriptionPlan.objects.get(id=value, is_active=True)
            except SubscriptionPlan.DoesNotExist:
                raise serializers.ValidationError("Тарифный план не найден.")
        return value

