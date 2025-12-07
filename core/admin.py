from django.contrib import admin
from .models import Dish


@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    """Админ-панель для блюд"""
    list_display = ['name', 'weight', 'calories', 'proteins', 'fats', 'carbohydrates', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
