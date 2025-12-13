"""
Views for core app.
"""
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.dateparse import parse_date
from django.utils import timezone
from decimal import Decimal

from .models import Dish, DailyGoal, Meal
from .serializers import (
    DishSerializer, 
    DailyGoalSerializer, 
    AutoCalculateGoalsSerializer,
    DishRecognitionSerializer,
    FoodSearchSerializer
)
from .utils import auto_calculate_goals, search_food_nutrition
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
    # Пагинация для списка блюд (по умолчанию из settings.py - 20 элементов)
    # Можно переопределить через query параметр ?page_size=N
    
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
        
        # Сохраняем блюдо с user и meal
        # Удаляем date и meal_type из validated_data перед сохранением
        validated_data = serializer.validated_data.copy()
        # Удаляем поля, которые не являются полями модели Dish
        validated_data.pop('date', None)
        validated_data.pop('meal_type', None)
        
        # Убеждаемся, что вес указан
        if 'weight' not in validated_data or validated_data['weight'] is None:
            validated_data['weight'] = 100
        
        # Получаем значения КБЖУ (если не указаны, считаем их равными 0)
        dish_name = validated_data.get('name', '').strip()
        dish_weight = int(validated_data.get('weight', 100))
        
        # ВАЖНО: проверяем, были ли КБЖУ переданы вообще (None) или переданы как 0
        # Если поля отсутствуют в validated_data, значит они не были отправлены
        calories_raw = validated_data.get('calories', None)
        proteins_raw = validated_data.get('proteins', None)
        fats_raw = validated_data.get('fats', None)
        carbohydrates_raw = validated_data.get('carbohydrates', None)
        
        # Если поля не переданы или равны 0, считаем что КБЖУ не указаны
        calories = int(calories_raw) if calories_raw is not None else 0
        proteins_raw = proteins_raw if proteins_raw is not None else None
        fats_raw = fats_raw if fats_raw is not None else None
        carbohydrates_raw = carbohydrates_raw if carbohydrates_raw is not None else None
        
        # Преобразуем в Decimal, если указаны, иначе 0
        if proteins_raw is not None:
            proteins = Decimal(str(proteins_raw)) if not isinstance(proteins_raw, Decimal) else proteins_raw
        else:
            proteins = Decimal('0')
        
        if fats_raw is not None:
            fats = Decimal(str(fats_raw)) if not isinstance(fats_raw, Decimal) else fats_raw
        else:
            fats = Decimal('0')
        
        if carbohydrates_raw is not None:
            carbohydrates = Decimal(str(carbohydrates_raw)) if not isinstance(carbohydrates_raw, Decimal) else carbohydrates_raw
        else:
            carbohydrates = Decimal('0')
        
        # Преобразуем Decimal в float для корректного сравнения с нулем
        proteins_float = float(proteins)
        fats_float = float(fats)
        carbohydrates_float = float(carbohydrates)
        
        # ВСЕГДА пытаемся найти КБЖУ автоматически, если они не указаны (все равны 0) и есть название блюда
        # Проверяем: либо поля не были переданы (None), либо были переданы как 0
        kbru_not_provided = (
            (calories_raw is None or calories == 0) and
            (proteins_raw is None or proteins_float == 0) and
            (fats_raw is None or fats_float == 0) and
            (carbohydrates_raw is None or carbohydrates_float == 0) and
            dish_name
        )
        
        if kbru_not_provided:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"🔍 Автоматический поиск КБЖУ для блюда: '{dish_name}' ({dish_weight}г)")
            
            nutrition_data = search_food_nutrition(dish_name, dish_weight)
            if nutrition_data:
                calories = int(nutrition_data.get('calories', 0))
                proteins = Decimal(str(nutrition_data.get('proteins', 0)))
                fats = Decimal(str(nutrition_data.get('fats', 0)))
                carbohydrates = Decimal(str(nutrition_data.get('carbohydrates', 0)))
                logger.info(f"✅ КБЖУ найдены автоматически: {calories} ккал, Б: {proteins}г, Ж: {fats}г, У: {carbohydrates}г")
            else:
                logger.warning(f"❌ Не удалось найти КБЖУ для блюда: '{dish_name}'")
        
        # Создаем блюдо напрямую через модель, чтобы избежать проблем с date и meal_type в serializer
        from .models import Dish
        dish = Dish.objects.create(
            user=user,
            meal=meal,
            name=dish_name,
            weight=dish_weight,
            calories=calories,
            proteins=proteins,
            fats=fats,
            carbohydrates=carbohydrates,
        )
        
        # Обновляем instance в serializer для правильного ответа
        serializer.instance = dish
    
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
        
        # Получаем все блюда за день с оптимизацией запросов
        # prefetch_related загружает все dishes одним запросом
        meals = Meal.objects.filter(
            user=user, 
            date=date_obj
        ).prefetch_related('dishes').order_by('meal_type')
        
        # Группируем блюда по типам приёмов пищи
        meals_data = {
            'breakfast': [],
            'lunch': [],
            'dinner': [],
            'snack': []
        }
        
        all_dishes = []
        # Используем prefetch_related, поэтому dishes.all() не делает дополнительных запросов
        for meal in meals:
            dishes = meal.dishes.all()
            # Сериализуем все блюда разом для эффективности
            dishes_serialized = DishSerializer(dishes, many=True).data
            meals_data[meal.meal_type].extend(dishes_serialized)
            all_dishes.extend(dishes)
        
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
    
    def get_throttles(self):
        """Применяем throttling для распознавания"""
        from core.throttles import DishRecognitionThrottle
        return [DishRecognitionThrottle()]
    
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
        
        # Проверяем, что данные не пустые
        if not base64_data or len(base64_data) < 100:
            return Response(
                {"detail": "Изображение слишком маленькое или повреждено."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверяем максимальный размер base64 строки (примерно 13.3 МБ в base64 = 10 МБ бинарных данных)
        max_base64_size = 14 * 1024 * 1024  # 14 МБ для учёта overhead base64
        if len(base64_data) > max_base64_size:
            return Response(
                {"detail": "Размер изображения не должен превышать 10 МБ."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
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
            from PIL import Image
            import io
            
            # Декодируем изображение для проверки
            try:
                image_bytes = base64.b64decode(base64_data, validate=True)
            except Exception as e:
                return Response(
                    {"detail": "Неверный формат base64."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Проверяем, что это действительно изображение
            import logging
            logger = logging.getLogger(__name__)
            try:
                # Проверяем размер декодированного изображения
                if len(image_bytes) > 10 * 1024 * 1024:  # 10 МБ
                    return Response(
                        {"detail": "Размер изображения не должен превышать 10 МБ."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                # Проверяем формат изображения
                img = Image.open(io.BytesIO(image_bytes))
                img.verify()
                # После verify() нужно открыть заново
                img = Image.open(io.BytesIO(image_bytes))
                # Проверяем, что это поддерживаемый формат
                if img.format not in ['JPEG', 'PNG', 'WEBP', 'JPG']:
                    return Response(
                        {"detail": "Неверный формат изображения. Поддерживаются только JPEG, PNG и WebP."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except Exception as e:
                logger.error(f"Ошибка проверки изображения: {str(e)}")
                return Response(
                    {"detail": "Неверный формат изображения. Ожидается изображение в формате JPEG, PNG или WebP."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Используем OpenRouter API с моделью для распознавания изображений
            # Используем модель, которая поддерживает vision (например, gpt-4-vision-preview или claude-3-opus)
            url = "https://openrouter.ai/api/v1/chat/completions"
            
            site_url = getattr(settings, 'SITE_URL', 'http://217.26.29.106')
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json; charset=utf-8",
                "HTTP-Referer": site_url,
                "X-Title": "Calorio - Распознавание блюд",
            }
            
            # Логируем для отладки (без ключа)
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Отправка запроса к OpenRouter API, модель: openai/gpt-4o, размер изображения: {len(base64_data)} символов")
            
            # Формируем промпт для распознавания блюда (на английском для избежания проблем с кодировкой)
            prompt = """Analyze this food image and determine:
1. Dish name (in Russian language)
2. Approximate portion weight in grams
3. Calories (kcal)
4. Proteins (g)
5. Fats (g)
6. Carbohydrates (g)

Respond ONLY in JSON format without any additional comments or markdown:
{
  "name": "dish name in Russian",
  "weight": weight_in_grams,
  "calories": calories,
  "proteins": proteins,
  "fats": fats,
  "carbohydrates": carbohydrates
}

If you cannot determine exact values, use realistic estimates based on typical values for similar dishes."""
            
            # Пробуем разные модели для лучшей совместимости
            # Сначала пробуем GPT-4o, если не сработает - попробуем другие
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
                "max_tokens": 1000,  # Увеличиваем для более детальных ответов
                "temperature": 0.1,  # Очень низкая температура для точных результатов
            }
            
            # Отправляем запрос с явной обработкой UTF-8
            # Проблема: requests может использовать latin-1, поэтому делаем вручную
            import json as json_lib
            
            # Сериализуем в JSON с ensure_ascii=False
            json_str = json_lib.dumps(payload, ensure_ascii=False)
            json_bytes = json_str.encode('utf-8')
            
            # Обновляем заголовки для правильной отправки
            headers_final = headers.copy()
            headers_final['Content-Type'] = 'application/json; charset=utf-8'
            headers_final['Content-Length'] = str(len(json_bytes))
            
            # Отправляем как bytes
            response = requests.post(
                url,
                headers=headers_final,
                data=json_bytes,
                timeout=60
            )
            
            # Устанавливаем кодировку ответа
            response.encoding = 'utf-8'
            
            # Проверяем статус ответа
            if response.status_code != 200:
                import logging
                logger = logging.getLogger(__name__)
                try:
                    error_data = response.json()
                    error_text = str(error_data).replace(api_key, '***HIDDEN***')[:500]
                except:
                    try:
                        error_text = response.text[:500]
                    except:
                        error_text = "Не удалось прочитать ответ"
                logger.error(f"OpenRouter API вернул статус {response.status_code}: {error_text}")
                
                # Возвращаем понятное сообщение пользователю
                if response.status_code == 401:
                    return Response(
                        {"detail": "Ошибка авторизации в сервисе распознавания. Проверьте настройки API ключа."},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE
                    )
                elif response.status_code == 429:
                    return Response(
                        {"detail": "Превышен лимит запросов к сервису распознавания. Попробуйте позже."},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE
                    )
                else:
                    return Response(
                        {"detail": "Не удалось распознать блюдо. Попробуйте ещё раз."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            
            # Парсим JSON ответа с правильной кодировкой
            try:
                result = response.json()
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Ошибка парсинга JSON ответа: {str(e)}")
                # Пробуем декодировать вручную
                try:
                    result = json.loads(response.content.decode('utf-8'))
                except Exception as e2:
                    logger.error(f"Ошибка декодирования ответа: {str(e2)}")
                    raise ValueError(f"Не удалось распарсить ответ от API: {str(e2)}")
            
            # Извлекаем ответ из API
            if 'choices' in result and len(result['choices']) > 0:
                # Получаем content, убеждаясь что это строка в UTF-8
                content_raw = result['choices'][0]['message']['content']
                if isinstance(content_raw, bytes):
                    content = content_raw.decode('utf-8')
                else:
                    content = str(content_raw)
                
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
                
        except requests.exceptions.HTTPError as e:
            import logging
            logger = logging.getLogger(__name__)
            if e.response:
                try:
                    error_text = e.response.content.decode('utf-8')[:200]
                except:
                    error_text = "Не удалось декодировать ответ"
                error_msg = f"HTTP {e.response.status_code}: {error_text}"
            else:
                error_msg = str(e)
            logger.error(f"HTTP ошибка при обращении к OpenRouter: {error_msg}")
            
            if e.response and e.response.status_code == 401:
                return Response(
                    {"detail": "Ошибка авторизации в сервисе распознавания. Проверьте настройки API ключа."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            elif e.response and e.response.status_code == 429:
                return Response(
                    {"detail": "Превышен лимит запросов к сервису распознавания. Попробуйте позже."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            else:
                return Response(
                    {"detail": f"Ошибка сервиса распознавания: {error_msg}"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
        except requests.exceptions.RequestException as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Ошибка при обращении к сервису распознавания: {str(e)}")
            return Response(
                {"detail": f"Ошибка при обращении к сервису распознавания: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except json.JSONDecodeError as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Ошибка парсинга JSON при распознавании: {str(e)}, content: {content[:200] if 'content' in locals() else 'N/A'}")
            return Response(
                {"detail": "Не удалось распознать блюдо. Ответ API содержит некорректный JSON."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except ValueError as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Ошибка валидации данных при распознавании: {str(e)}")
            return Response(
                {"detail": "Не удалось распознать блюдо. Некорректные данные от API."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except KeyError as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Отсутствует ключ в ответе API: {str(e)}")
            return Response(
                {"detail": "Не удалось распознать блюдо. Неполный ответ от API."},
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


class FoodSearchView(generics.CreateAPIView):
    """View для поиска КБЖУ по названию продукта"""
    serializer_class = FoodSearchSerializer
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        """Поиск КБЖУ по названию продукта"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        food_name = serializer.validated_data['food_name']
        weight = serializer.validated_data.get('weight', 100)
        
        # Ищем КБЖУ через OpenRouter API (LLM)
        nutrition_data = search_food_nutrition(food_name, weight)
        
        if nutrition_data:
            return Response(nutrition_data, status=status.HTTP_200_OK)
        else:
            return Response(
                {"detail": "Не удалось найти информацию о продукте. Попробуйте другое название или введите КБЖУ вручную."},
                status=status.HTTP_404_NOT_FOUND
            )
