from rest_framework import serializers
from .models import Dish


class DishSerializer(serializers.ModelSerializer):
    """Сериализатор для блюда"""
    
    class Meta:
        model = Dish
        fields = (
            'id', 'name', 'weight', 'calories', 'proteins', 'fats', 
            'carbohydrates', 'created_at'
        )
        read_only_fields = ('id', 'created_at')

