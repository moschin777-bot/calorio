"""
Views for core app.
"""
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.db.models import Sum, Q
from decimal import Decimal
from datetime import date as date_type

from .models import Dish, DailyGoal, Meal
from .serializers import (
    DishSerializer, 
    DailyGoalSerializer, 
    AutoCalculateGoalsSerializer,
    DishRecognitionSerializer
)
from .utils import auto_calculate_goals
from django.views.generic import TemplateView
from django.conf import settings
from django.views.decorators.cache import never_cache
from pathlib import Path


class ReactAppView(TemplateView):
    """View to serve React app for all non-API routes."""
    template_name = 'index.html'
    
    @never_cache
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
    def get_template_names(self):
        """Return template path based on whether frontend is built."""
        frontend_dir = Path(settings.BASE_DIR) / 'frontend' / 'dist'
        if (frontend_dir / 'index.html').exists():
            return ['index.html']
        # Fallback if frontend not built yet
        return ['index.html']


class DishViewSet(viewsets.ModelViewSet):
    """ViewSet для управления блюдами"""
    serializer_class = DishSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Возвращает только блюда текущего пользователя"""
        user = self.request.user
        queryset = Dish.objects.filter(user=user).select_related('meal')
        
        # Фильтрация по дате через query параметр
        date_param = self.request.query_params.get('date', None)
        if date_param:
            try:
                date_obj = parse_date(date_param)
                if date_obj:
                    queryset = queryset.filter(meal__date=date_obj)
            except (ValueError, TypeError):
                pass
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """Создание блюда с привязкой к пользователю и приёму пищи"""
        user = self.request.user
        date_str = serializer.validated_data.get('date')
        meal_type = serializer.validated_data.get('meal_type')
        
        if not date_str or not meal_type:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Дата и тип приёма пищи обязательны.")
        
        # Парсим дату
        date_obj = parse_date(str(date_str))
        if not date_obj:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Неверный формат даты. Используйте YYYY-MM-DD.")
        
        # Находим или создаём приём пищи
        meal, created = Meal.objects.get_or_create(
            user=user,
            date=date_obj,
            meal_type=meal_type,
            defaults={}
        )
        
        # Создаём блюдо
        serializer.save(user=user, meal=meal)
    
    def get_object(self):
        """Получение объекта с проверкой прав доступа"""
        obj = super().get_object()
        if obj.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        return obj


class DailyGoalView(generics.RetrieveUpdateAPIView, generics.CreateAPIView):
    """View для получения и создания/обновления целей КБЖУ на день"""
    serializer_class = DailyGoalSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        """Получение цели на указанную дату"""
        date_str = self.kwargs.get('date')
        date_obj = parse_date(date_str)
        
        if not date_obj:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"date": ["Неверный формат даты. Используйте YYYY-MM-DD."]})
        
        try:
            goal = DailyGoal.objects.get(user=self.request.user, date=date_obj)
            return goal
        except DailyGoal.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("Цель на указанную дату не найдена.")
    
    def post(self, request, *args, **kwargs):
        """Создание или обновление цели (upsert)"""
        date_str = kwargs.get('date')
        date_obj = parse_date(date_str)
        
        if not date_obj:
            return Response(
                {"date": ["Неверный формат даты. Используйте YYYY-MM-DD."]},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверяем, существует ли цель
        goal, created = DailyGoal.objects.get_or_create(
            user=request.user,
            date=date_obj,
            defaults={}
        )
        
        serializer = self.get_serializer(goal, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(serializer.data, status=status_code)


class AutoCalculateGoalsView(generics.CreateAPIView):
    """View для автоматического расчёта целей КБЖУ"""
    serializer_class = AutoCalculateGoalsSerializer
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        """Расчёт и сохранение целей"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        date_obj = validated_data['date']
        
        # Рассчитываем цели
        calculated = auto_calculate_goals(
            weight=float(validated_data['weight']),
            height=validated_data['height'],
            age=validated_data['age'],
            activity_level=validated_data['activity_level'],
            gender=validated_data.get('gender', 'male'),
            goal=validated_data.get('goal', 'maintain')
        )
        
        # Создаём или обновляем цель
        goal, created = DailyGoal.objects.update_or_create(
            user=request.user,
            date=date_obj,
            defaults={
                'calories': calculated['calories'],
                'proteins': calculated['proteins'],
                'fats': calculated['fats'],
                'carbohydrates': calculated['carbohydrates'],
                'is_auto_calculated': True
            }
        )
        
        response_serializer = DailyGoalSerializer(goal)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(response_serializer.data, status=status_code)


class DayDataView(generics.RetrieveAPIView):
    """View для получения всех данных за день"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        """Получение данных за день"""
        date_str = kwargs.get('date')
        date_obj = parse_date(date_str)
        
        if not date_obj:
            return Response(
                {"date": ["Неверный формат даты. Используйте YYYY-MM-DD."]},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        
        # Получаем цель
        try:
            goal = DailyGoal.objects.get(user=user, date=date_obj)
            goal_data = DailyGoalSerializer(goal).data
        except DailyGoal.DoesNotExist:
            goal_data = None
        
        # Получаем все блюда за день
        meals = Meal.objects.filter(user=user, date=date_obj).prefetch_related('dishes')
        
        # Группируем блюда по типам приёмов пищи
        meals_data = {
            'breakfast': [],
            'lunch': [],
            'dinner': [],
            'snack': []
        }
        
        all_dishes = []
        for meal in meals:
            dishes = meal.dishes.all()
            for dish in dishes:
                dish_data = DishSerializer(dish).data
                meals_data[meal.meal_type].append(dish_data)
                all_dishes.append(dish)
        
        # Рассчитываем суммарные значения КБЖУ
        total_calories = sum(int(dish.calories or 0) for dish in all_dishes)
        total_proteins = sum(float(dish.proteins or 0) for dish in all_dishes)
        total_fats = sum(float(dish.fats or 0) for dish in all_dishes)
        total_carbohydrates = sum(float(dish.carbohydrates or 0) for dish in all_dishes)
        
        # Рассчитываем проценты выполнения целей
        goal_progress = {
            'calories_percent': Decimal('0.0'),
            'proteins_percent': Decimal('0.0'),
            'fats_percent': Decimal('0.0'),
            'carbohydrates_percent': Decimal('0.0'),
        }
        
        if goal_data:
            goal_calories = goal_data.get('calories', 0)
            goal_proteins = float(goal_data.get('proteins', 0))
            goal_fats = float(goal_data.get('fats', 0))
            goal_carbohydrates = float(goal_data.get('carbohydrates', 0))
            
            if goal_calories > 0:
                goal_progress['calories_percent'] = Decimal(str((total_calories / goal_calories) * 100))
            if goal_proteins > 0:
                goal_progress['proteins_percent'] = Decimal(str((total_proteins / goal_proteins) * 100))
            if goal_fats > 0:
                goal_progress['fats_percent'] = Decimal(str((total_fats / goal_fats) * 100))
            if goal_carbohydrates > 0:
                goal_progress['carbohydrates_percent'] = Decimal(str((total_carbohydrates / goal_carbohydrates) * 100))
        
        # Преобразуем Decimal в float для JSON сериализации
        return Response({
            'date': date_str,
            'goal': goal_data,
            'meals': meals_data,
            'summary': {
                'total_calories': int(total_calories),
                'total_proteins': float(total_proteins),
                'total_fats': float(total_fats),
                'total_carbohydrates': float(total_carbohydrates),
                'goal_progress': {
                    'calories_percent': float(goal_progress['calories_percent']),
                    'proteins_percent': float(goal_progress['proteins_percent']),
                    'fats_percent': float(goal_progress['fats_percent']),
                    'carbohydrates_percent': float(goal_progress['carbohydrates_percent']),
                }
            }
        })


class DishRecognitionView(generics.CreateAPIView):
    """View для распознавания блюда по фотографии"""
    serializer_class = DishRecognitionSerializer
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        """Распознавание блюда через OpenRouter API"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        image_base64 = serializer.validated_data['image_base64']
        
        # Извлекаем base64 данные (убираем префикс если есть)
        if ',' in image_base64:
            base64_data = image_base64.split(',')[-1]
        else:
            base64_data = image_base64
        
        # Получаем API ключ из настроек
        from django.conf import settings
        api_key = getattr(settings, 'OPENROUTER_API_KEY', '')
        
        if not api_key:
            return Response(
                {"detail": "Сервис распознавания временно недоступен."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        try:
            import requests
            import json
            import base64
            
            # Декодируем изображение для проверки размера
            image_bytes = base64.b64decode(base64_data)
            
            # Используем OpenRouter API с моделью для распознавания изображений
            # Используем модель, которая поддерживает vision (например, gpt-4-vision-preview или claude-3-opus)
            url = "https://openrouter.ai/api/v1/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": getattr(settings, 'SITE_URL', 'http://217.26.29.106'),
            }
            
            # Формируем промпт для распознавания блюда
            prompt = """Проанализируй это изображение еды и определи:
1. Название блюда (на русском языке)
2. Примерный вес порции в граммах
3. Калории (ккал)
4. Белки (г)
5. Жиры (г)
6. Углеводы (г)

Ответь ТОЛЬКО в формате JSON без дополнительных комментариев:
{
  "name": "название блюда",
  "weight": вес_в_граммах,
  "calories": калории,
  "proteins": белки,
  "fats": жиры,
  "carbohydrates": углеводы
}

Если не можешь определить точные значения, используй реалистичные оценки на основе типичных значений для подобных блюд."""
            
            payload = {
                "model": "openai/gpt-4o",  # Используем GPT-4o для лучшего распознавания
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_data}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 500,
                "temperature": 0.3,  # Низкая температура для более точных результатов
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            # Извлекаем ответ из API
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                
                # Парсим JSON из ответа
                import re
                # Ищем JSON в ответе (более надёжный способ)
                # Убираем markdown код блоки если есть
                content_cleaned = content.replace('```json', '').replace('```', '').strip()
                
                # Пробуем найти JSON объект (может быть вложенным)
                json_match = None
                # Сначала пробуем найти между первыми { и последними }
                start_idx = content_cleaned.find('{')
                end_idx = content_cleaned.rfind('}')
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_str = content_cleaned[start_idx:end_idx+1]
                    json_match = type('obj', (object,), {'group': lambda: json_str})()
                
                if json_match:
                    try:
                        dish_data = json.loads(json_match.group())
                    except json.JSONDecodeError:
                        # Если не получилось, пробуем очистить строку от markdown
                        cleaned = json_match.group().replace('```json', '').replace('```', '').strip()
                        dish_data = json.loads(cleaned)
                    
                    # Валидация и округление данных
                    recognized_dish = {
                        "name": str(dish_data.get("name", "Неизвестное блюдо")).strip(),
                        "weight": max(1, int(float(dish_data.get("weight", 100)))),
                        "calories": max(0, int(float(dish_data.get("calories", 0)))),
                        "proteins": round(max(0, float(dish_data.get("proteins", 0))), 2),
                        "fats": round(max(0, float(dish_data.get("fats", 0))), 2),
                        "carbohydrates": round(max(0, float(dish_data.get("carbohydrates", 0))), 2),
                        "confidence": 0.8  # Уверенность распознавания
                    }
                    
                    return Response({
                        "recognized_dishes": [recognized_dish],
                        "suggested_date": serializer.validated_data.get('date', None),
                        "suggested_meal_type": serializer.validated_data.get('meal_type', None)
                    })
                else:
                    # Логируем для отладки
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Не удалось найти JSON в ответе: {content[:500]}")
                    raise ValueError("Не удалось извлечь JSON из ответа")
            else:
                raise ValueError("Неожиданный формат ответа от API")
                
        except requests.exceptions.RequestException as e:
            return Response(
                {"detail": f"Ошибка при обращении к сервису распознавания: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Ошибка парсинга JSON при распознавании: {str(e)}")
            return Response(
                {"detail": "Не удалось распознать блюдо. Попробуйте ещё раз."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Неожиданная ошибка при распознавании: {str(e)}", exc_info=True)
            return Response(
                {"detail": f"Ошибка распознавания: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
