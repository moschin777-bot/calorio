from rest_framework import viewsets, permissions, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from django.utils.dateparse import parse_date
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.db.models import Q
from .models import Dish, DailyGoal, Meal
from .serializers import (
    DishSerializer, 
    DailyGoalSerializer, 
    DishRecognitionSerializer,
    AutoCalculateGoalsSerializer
)
from .throttles import DishRecognitionThrottle
from .utils import auto_calculate_goals
import base64
import json
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)


class DishPagination(PageNumberPagination):
    """Пагинация для блюд"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class DishViewSet(viewsets.ModelViewSet):
    """ViewSet для управления блюдами с поиском, фильтрацией и пагинацией"""
    queryset = Dish.objects.all()
    serializer_class = DishSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = DishPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['created_at', 'calories', 'proteins', 'fats', 'carbohydrates']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Возвращаем только блюда текущего пользователя с фильтрацией"""
        queryset = Dish.objects.filter(user=self.request.user).select_related('meal', 'user')
        
        # Фильтрация по дате
        date_param = self.request.query_params.get('date', None)
        if date_param:
            try:
                date_obj = parse_date(date_param)
                if date_obj is None:
                    return Dish.objects.none()
                # Фильтруем по дате через связанный Meal
                queryset = queryset.filter(meal__date=date_obj)
            except (ValueError, TypeError):
                return Dish.objects.none()
        
        # Фильтрация по типу приёма пищи
        meal_type_param = self.request.query_params.get('meal_type', None)
        if meal_type_param:
            queryset = queryset.filter(meal__meal_type=meal_type_param)
        
        # Поиск по названию (через search_fields уже реализован, но можно добавить дополнительную логику)
        search_param = self.request.query_params.get('search', None)
        if search_param:
            queryset = queryset.filter(name__icontains=search_param)
        
        return queryset
    
    def get_object(self):
        """Получение конкретного блюда с проверкой прав доступа"""
        obj = get_object_or_404(self.get_queryset(), pk=self.kwargs['pk'])
        # Дополнительная проверка, что блюдо принадлежит пользователю
        if obj.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        return obj
    
    def perform_create(self, serializer):
        """При создании блюда создаём или находим Meal и связываем с пользователем"""
        user = self.request.user
        date = serializer.validated_data.pop('date')
        meal_type = serializer.validated_data.pop('meal_type')
        
        # Получаем или создаём Meal для указанной даты и типа
        meal, created = Meal.objects.get_or_create(
            user=user,
            date=date,
            meal_type=meal_type,
            defaults={'user': user, 'date': date, 'meal_type': meal_type}
        )
        
        # Устанавливаем значения по умолчанию для необязательных полей
        # Обязательные: date, meal_type, name
        # Остальные по умолчанию 0 (weight не может быть 0, поэтому 1)
        weight = serializer.validated_data.get('weight')
        if weight is None:
            weight = 1  # weight не может быть 0, минимальное значение 1
        
        calories = serializer.validated_data.get('calories', 0)
        proteins = serializer.validated_data.get('proteins', 0)
        fats = serializer.validated_data.get('fats', 0)
        carbohydrates = serializer.validated_data.get('carbohydrates', 0)
        
        # Преобразуем None в Decimal для consistency
        from decimal import Decimal
        if proteins is None:
            proteins = Decimal('0.00')
        else:
            proteins = Decimal(str(proteins))
        if fats is None:
            fats = Decimal('0.00')
        else:
            fats = Decimal(str(fats))
        if carbohydrates is None:
            carbohydrates = Decimal('0.00')
        else:
            carbohydrates = Decimal(str(carbohydrates))
        
        serializer.save(
            user=user,
            meal=meal,
            weight=weight,
            calories=calories,
            proteins=proteins,
            fats=fats,
            carbohydrates=carbohydrates
        )
    
    def perform_update(self, serializer):
        """При обновлении блюда обновляем связь с Meal, если изменились date или meal_type"""
        instance = self.get_object()
        user = self.request.user
        
        # Проверяем, изменились ли date или meal_type
        date = serializer.validated_data.get('date')
        meal_type = serializer.validated_data.get('meal_type')
        
        # Если date или meal_type не указаны, используем текущие значения из Meal
        if date is None and instance.meal:
            date = instance.meal.date
        if meal_type is None and instance.meal:
            meal_type = instance.meal.meal_type
        
        # Если date или meal_type изменились, обновляем Meal
        if date and meal_type:
            if not instance.meal or instance.meal.date != date or instance.meal.meal_type != meal_type:
                meal, created = Meal.objects.get_or_create(
                    user=user,
                    date=date,
                    meal_type=meal_type,
                    defaults={'user': user, 'date': date, 'meal_type': meal_type}
                )
                serializer.save(meal=meal)
            else:
                serializer.save()
        else:
            serializer.save()
    
    def destroy(self, request, *args, **kwargs):
        """Удаление блюда с проверкой прав доступа"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DailyGoalView(APIView):
    """API для получения и создания/обновления целей КБЖУ на день"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, date):
        """
        Получение цели КБЖУ на указанную дату
        GET /api/goals/{date}/
        """
        try:
            date_obj = parse_date(date)
            if date_obj is None:
                return Response(
                    {"date": ["Неверный формат даты. Используйте YYYY-MM-DD."]},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {"date": ["Неверный формат даты. Используйте YYYY-MM-DD."]},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            goal = DailyGoal.objects.get(user=request.user, date=date_obj)
            serializer = DailyGoalSerializer(goal)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except DailyGoal.DoesNotExist:
            return Response(
                {"detail": "Цель на указанную дату не найдена."},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def post(self, request, date):
        """
        Создание или обновление цели КБЖУ на указанную дату
        POST /api/goals/{date}/
        """
        try:
            date_obj = parse_date(date)
            if date_obj is None:
                return Response(
                    {"date": ["Неверный формат даты. Используйте YYYY-MM-DD."]},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {"date": ["Неверный формат даты. Используйте YYYY-MM-DD."]},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверяем, существует ли уже цель на эту дату
        try:
            goal = DailyGoal.objects.get(user=request.user, date=date_obj)
            created = False
        except DailyGoal.DoesNotExist:
            goal = None
            created = True
        
        # Валидируем данные
        serializer = DailyGoalSerializer(goal, data=request.data, partial=False)
        
        if serializer.is_valid():
            serializer.save(user=request.user, date=date_obj, is_auto_calculated=False)
            status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
            return Response(serializer.data, status=status_code)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DayDataView(APIView):
    """
    API для получения всех данных за день
    GET /api/days/{date}/
    
    Возвращает:
    - Цель КБЖУ на день
    - Блюда, сгруппированные по приёмам пищи
    - Суммарную статистику КБЖУ
    - Процент выполнения целей
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, date):
        """Получение данных за выбранный день"""
        try:
            date_obj = parse_date(date)
            if date_obj is None:
                return Response(
                    {"date": ["Неверный формат даты. Используйте YYYY-MM-DD."]},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {"date": ["Неверный формат даты. Используйте YYYY-MM-DD."]},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Получаем цель на день (если есть)
        try:
            goal = DailyGoal.objects.get(user=request.user, date=date_obj)
            goal_data = DailyGoalSerializer(goal).data
        except DailyGoal.DoesNotExist:
            goal_data = None
        
        # Получаем все блюда за день
        dishes = Dish.objects.filter(
            user=request.user,
            meal__date=date_obj
        ).select_related('meal')
        
        # Группируем блюда по типам приёмов пищи
        meals_data = {
            'breakfast': [],
            'lunch': [],
            'dinner': [],
            'snack': [],
        }
        
        for dish in dishes:
            if dish.meal:
                meal_type = dish.meal.meal_type
                dish_data = DishSerializer(dish).data
                meals_data[meal_type].append(dish_data)
        
        # Рассчитываем суммарные значения КБЖУ
        # Используем Decimal для точных расчётов
        from decimal import Decimal
        total_calories = sum(dish.calories for dish in dishes)
        total_proteins = sum(Decimal(str(dish.proteins)) for dish in dishes)
        total_fats = sum(Decimal(str(dish.fats)) for dish in dishes)
        total_carbohydrates = sum(Decimal(str(dish.carbohydrates)) for dish in dishes)
        
        # Рассчитываем процент выполнения целей
        goal_progress = {
            'calories_percent': 0,
            'proteins_percent': 0,
            'fats_percent': 0,
            'carbohydrates_percent': 0,
        }
        
        if goal_data:
            if int(goal_data['calories']) > 0:
                goal_progress['calories_percent'] = round(
                    (total_calories / int(goal_data['calories'])) * 100, 2
                )
            if float(goal_data['proteins']) > 0:
                goal_progress['proteins_percent'] = round(
                    (float(total_proteins) / float(goal_data['proteins'])) * 100, 2
                )
            if float(goal_data['fats']) > 0:
                goal_progress['fats_percent'] = round(
                    (float(total_fats) / float(goal_data['fats'])) * 100, 2
                )
            if float(goal_data['carbohydrates']) > 0:
                goal_progress['carbohydrates_percent'] = round(
                    (float(total_carbohydrates) / float(goal_data['carbohydrates'])) * 100, 2
                )
        
        # Формируем ответ
        response_data = {
            'date': date,
            'goal': goal_data,
            'meals': meals_data,
            'summary': {
                'total_calories': total_calories,
                'total_proteins': float(total_proteins),
                'total_fats': float(total_fats),
                'total_carbohydrates': float(total_carbohydrates),
                'goal_progress': goal_progress,
            }
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


class AutoCalculateGoalsView(APIView):
    """
    API для автоматического расчёта целей КБЖУ
    POST /api/goals/auto-calculate/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """
        Автоматический расчёт целей КБЖУ на основе параметров пользователя
        """
        serializer = AutoCalculateGoalsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Извлекаем валидированные данные
        weight = float(serializer.validated_data['weight'])
        height = serializer.validated_data['height']
        age = serializer.validated_data['age']
        activity_level = serializer.validated_data['activity_level']
        gender = serializer.validated_data.get('gender', 'male')
        goal = serializer.validated_data.get('goal', 'maintain')
        date = serializer.validated_data['date']
        
        # Рассчитываем цели
        calculated_goals = auto_calculate_goals(
            weight=weight,
            height=height,
            age=age,
            activity_level=activity_level,
            gender=gender,
            goal=goal
        )
        
        # Создаём или обновляем цель на указанную дату
        daily_goal, created = DailyGoal.objects.update_or_create(
            user=request.user,
            date=date,
            defaults={
                'calories': calculated_goals['calories'],
                'proteins': calculated_goals['proteins'],
                'fats': calculated_goals['fats'],
                'carbohydrates': calculated_goals['carbohydrates'],
                'is_auto_calculated': True,
            }
        )
        
        # Возвращаем результат
        goal_serializer = DailyGoalSerializer(daily_goal)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(goal_serializer.data, status=status_code)


class DishRecognitionView(APIView):
    """
    API для распознавания блюда по фотографии
    POST /api/dishes/recognize/
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [DishRecognitionThrottle]
    
    def post(self, request):
        """
        Распознавание блюда по изображению в формате base64
        """
        # Валидация входных данных
        serializer = DishRecognitionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        image_base64 = serializer.validated_data['image_base64']
        
        # Получаем опциональные поля date и meal_type
        from django.utils import timezone
        suggested_date = serializer.validated_data.get('date')
        if suggested_date is None:
            suggested_date = timezone.now().date()
        else:
            suggested_date = suggested_date
        
        suggested_meal_type = serializer.validated_data.get('meal_type', '')
        
        # Извлекаем base64 данные (убираем префикс если есть)
        if ',' in image_base64:
            base64_data = image_base64.split(',')[-1]
        else:
            base64_data = image_base64
        
        # Декодируем base64
        try:
            image_bytes = base64.b64decode(base64_data)
        except Exception as e:
            logger.error(f"Ошибка декодирования base64: {e}")
            return Response(
                {"image_base64": ["Неверный формат base64."]},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Формируем data URL для отправки в API
        # Определяем MIME тип изображения
        from PIL import Image
        import io
        try:
            img = Image.open(io.BytesIO(image_bytes))
            mime_type = f"image/{img.format.lower()}" if img.format else "image/jpeg"
        except Exception as e:
            logger.error(f"Ошибка определения типа изображения: {e}")
            mime_type = "image/jpeg"  # По умолчанию
        
        image_data_url = f"data:{mime_type};base64,{base64_data}"
        
        # Проверяем наличие API ключа
        if not settings.OPENROUTER_API_KEY:
            logger.error("OPENROUTER_API_KEY не настроен")
            return Response(
                {"detail": "Сервис распознавания временно недоступен."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        # Инициализируем клиент OpenAI для OpenRouter
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.OPENROUTER_API_KEY,
        )
        
        # Промпт для распознавания блюда
        prompt = """Проанализируй это изображение блюда и верни JSON с информацией о блюде.
Требования к ответу:
1. Ответ должен быть ТОЛЬКО валидным JSON объектом
2. JSON должен содержать следующие поля:
   - "name": строка с названием блюда
   - "weight": целое число (примерная масса в граммах)
   - "calories": целое число (калории в ккал)
   - "proteins": число с плавающей точкой (белки в граммах)
   - "fats": число с плавающей точкой (жиры в граммах)
   - "carbohydrates": число с плавающей точкой (углеводы в граммах)

Пример правильного ответа:
{
  "name": "Куриная грудка с рисом",
  "weight": 250,
  "calories": 350,
  "proteins": 35.5,
  "fats": 8.2,
  "carbohydrates": 30.0
}

ВАЖНО: Верни ТОЛЬКО JSON, без дополнительного текста, объяснений или markdown разметки."""
        
        # Пытаемся получить валидный JSON (до 3 попыток)
        max_attempts = 3
        last_error = None
        
        for attempt in range(max_attempts):
            try:
                completion = client.chat.completions.create(
                    extra_headers={
                        "HTTP-Referer": "https://calorio.app",
                        "X-Title": "Calorio",
                    },
                    model="google/gemini-2.0-flash-exp:free",
                    messages=[
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
                                        "url": image_data_url
                                    }
                                }
                            ]
                        }
                    ]
                )
                
                response_text = completion.choices[0].message.content.strip()
                
                # Пытаемся извлечь JSON из ответа (может быть обернут в markdown или текст)
                # Убираем markdown код блоки если есть
                if response_text.startswith("```"):
                    # Убираем первую строку с ```json или ```
                    lines = response_text.split('\n')
                    if lines[0].startswith('```'):
                        lines = lines[1:]
                    # Убираем последнюю строку с ```
                    if lines and lines[-1].strip() == '```':
                        lines = lines[:-1]
                    response_text = '\n'.join(lines)
                
                # Парсим JSON
                try:
                    result_json = json.loads(response_text)
                    
                    # Валидируем структуру JSON
                    required_fields = ['name', 'weight', 'calories', 'proteins', 'fats', 'carbohydrates']
                    if not all(field in result_json for field in required_fields):
                        raise ValueError("Отсутствуют обязательные поля в JSON")
                    
                    # Проверяем типы данных
                    if not isinstance(result_json['name'], str):
                        raise ValueError("Поле 'name' должно быть строкой")
                    if not isinstance(result_json['weight'], int) or result_json['weight'] < 1:
                        raise ValueError("Поле 'weight' должно быть целым числом >= 1")
                    if not isinstance(result_json['calories'], int) or result_json['calories'] < 0:
                        raise ValueError("Поле 'calories' должно быть целым числом >= 0")
                    if not isinstance(result_json['proteins'], (int, float)) or result_json['proteins'] < 0:
                        raise ValueError("Поле 'proteins' должно быть числом >= 0")
                    if not isinstance(result_json['fats'], (int, float)) or result_json['fats'] < 0:
                        raise ValueError("Поле 'fats' должно быть числом >= 0")
                    if not isinstance(result_json['carbohydrates'], (int, float)) or result_json['carbohydrates'] < 0:
                        raise ValueError("Поле 'carbohydrates' должно быть числом >= 0")
                    
                    # Формируем ответ согласно документации API
                    # Добавляем confidence (уверенность распознавания)
                    # Для простоты устанавливаем confidence = 1.0, так как API не возвращает это значение
                    confidence = 1.0
                    
                    # Формируем объект распознанного блюда
                    recognized_dish = {
                        "name": result_json['name'],
                        "weight": result_json['weight'],
                        "calories": result_json['calories'],
                        "proteins": float(result_json['proteins']),
                        "fats": float(result_json['fats']),
                        "carbohydrates": float(result_json['carbohydrates']),
                        "confidence": confidence
                    }
                    
                    # Формируем ответ согласно документации
                    response_data = {
                        "recognized_dishes": [recognized_dish],
                        "suggested_date": suggested_date.strftime('%Y-%m-%d'),
                        "suggested_meal_type": suggested_meal_type
                    }
                    
                    return Response(response_data, status=status.HTTP_200_OK)
                    
                except json.JSONDecodeError as e:
                    last_error = f"Невалидный JSON на попытке {attempt + 1}: {e}"
                    logger.warning(f"{last_error}. Ответ: {response_text[:200]}")
                    if attempt < max_attempts - 1:
                        continue
                except ValueError as e:
                    last_error = f"Ошибка валидации JSON на попытке {attempt + 1}: {e}"
                    logger.warning(f"{last_error}. JSON: {result_json if 'result_json' in locals() else 'не распарсен'}")
                    if attempt < max_attempts - 1:
                        continue
                
            except Exception as e:
                last_error = f"Ошибка при обращении к API на попытке {attempt + 1}: {str(e)}"
                logger.error(last_error)
                if attempt < max_attempts - 1:
                    continue
        
        # Если все попытки не удались
        logger.error(f"Не удалось получить валидный JSON после {max_attempts} попыток. Последняя ошибка: {last_error}")
        return Response(
            {"detail": "Не удалось распознать блюдо. Попробуйте ещё раз."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

