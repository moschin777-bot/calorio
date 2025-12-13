"""
Утилиты для расчёта КБЖУ
"""
from decimal import Decimal


def calculate_bmr(weight, height, age, gender='male'):
    """
    Расчёт базального метаболизма (BMR) по формуле Миффлина-Сан Жеора
    
    Args:
        weight: вес в кг
        height: рост в см
        age: возраст в годах
        gender: пол ('male' или 'female')
    
    Returns:
        BMR в ккал/день
    """
    if gender == 'male':
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    
    return bmr


def calculate_tdee(bmr, activity_level):
    """
    Расчёт общего дневного расхода энергии (TDEE) на основе BMR и уровня активности
    
    Args:
        bmr: базальный метаболизм
        activity_level: уровень активности
            - 'sedentary': малоподвижный (коэффициент 1.2)
            - 'light': лёгкая активность (коэффициент 1.375)
            - 'moderate': умеренная активность (коэффициент 1.55)
            - 'active': высокая активность (коэффициент 1.725)
            - 'very_active': очень высокая активность (коэффициент 1.9)
    
    Returns:
        TDEE в ккал/день
    """
    activity_multipliers = {
        'sedentary': 1.2,
        'light': 1.375,
        'moderate': 1.55,
        'active': 1.725,
        'very_active': 1.9,
    }
    
    multiplier = activity_multipliers.get(activity_level, 1.2)
    tdee = bmr * multiplier
    
    return tdee


def calculate_macros(calories, weight=None):
    """
    Расчёт макронутриентов (белки, жиры, углеводы) на основе калорий
    
    Используется оптимальное распределение для здорового питания:
    - Белки: 1.6-2.2 г на кг веса (минимум 30% калорий, 4 ккал/г)
    - Жиры: 25-35% калорий (9 ккал/г)
    - Углеводы: остаток калорий (4 ккал/г)
    
    Точные значения калорийности:
    - Белки: 4 ккал/г
    - Жиры: 9 ккал/г
    - Углеводы: 4 ккал/г
    
    Args:
        calories: целевые калории в ккал
        weight: вес в кг (опционально, для более точного расчёта белков)
    
    Returns:
        dict с ключами 'proteins', 'fats', 'carbohydrates' в граммах
    """
    # Рассчитываем белки
    if weight:
        # Оптимальное количество белка: 1.8 г на кг веса
        proteins = weight * 1.8
        proteins_calories = proteins * 4  # 4 ккал на грамм белка
    else:
        # Если вес не указан, используем 30% калорий
        proteins_calories = calories * 0.30
        proteins = proteins_calories / 4
    
    # Жиры: 30% калорий (оптимально для здоровья)
    fats_calories = calories * 0.30
    fats = fats_calories / 9  # 9 ккал на грамм жира
    
    # Углеводы: остаток калорий
    carbs_calories = calories - proteins_calories - fats_calories
    carbohydrates = carbs_calories / 4  # 4 ккал на грамм углеводов
    
    # Округляем до 2 знаков после запятой
    return {
        'proteins': round(Decimal(str(proteins)), 2),
        'fats': round(Decimal(str(fats)), 2),
        'carbohydrates': round(Decimal(str(carbohydrates)), 2),
    }


def search_food_nutrition(food_name, weight_grams=100):
    """
    Поиск КБЖУ по названию продукта через OpenRouter API (LLM).
    
    Args:
        food_name: Название продукта/блюда
        weight_grams: Вес в граммах (по умолчанию 100г)
    
    Returns:
        dict: {
            'name': название продукта,
            'weight': вес в граммах,
            'calories': калории,
            'proteins': белки,
            'fats': жиры,
            'carbohydrates': углеводы
        } или None если не найдено
    """
    import requests
    import json
    import logging
    from django.conf import settings
    
    logger = logging.getLogger(__name__)
    
    # Получаем API ключ из настроек
    api_key = getattr(settings, 'OPENROUTER_API_KEY', '')
    
    if not api_key:
        logger.warning("OpenRouter API ключ не настроен")
        return None
    
    try:
        # Используем OpenRouter API для определения КБЖУ по названию
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        site_url = getattr(settings, 'SITE_URL', 'http://217.26.29.106')
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json; charset=utf-8",
            "HTTP-Referer": site_url,
            "X-Title": "Calorio - Поиск КБЖУ",
        }
        
        # Формируем промпт для определения КБЖУ по названию блюда
        prompt = f"""Определи пищевую ценность (КБЖУ) для блюда/продукта: "{food_name}"

Вес порции: {weight_grams} грамм

Верни ТОЛЬКО JSON без дополнительных комментариев или markdown:
{{
  "name": "точное название блюда/продукта на русском",
  "weight": {weight_grams},
  "calories": калории_в_ккал_для_указанного_веса,
  "proteins": белки_в_граммах_для_указанного_веса,
  "fats": жиры_в_граммах_для_указанного_веса,
  "carbohydrates": углеводы_в_граммах_для_указанного_веса
}}

Используй реалистичные значения на основе типичных данных для подобных блюд/продуктов.
Если это сложное блюдо (например, "борщ"), рассчитай средние значения для типичной порции.
Все значения должны быть для указанного веса ({weight_grams}г), а не для 100г."""
        
        payload = {
            "model": "openai/gpt-4o-mini",  # Используем более дешевую модель для текстовых запросов
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 500,
            "temperature": 0.1,  # Низкая температура для точных результатов
        }
        
        # Сериализуем в JSON с ensure_ascii=False для поддержки русского языка
        json_str = json.dumps(payload, ensure_ascii=False)
        json_bytes = json_str.encode('utf-8')
        
        headers_final = headers.copy()
        headers_final['Content-Type'] = 'application/json; charset=utf-8'
        headers_final['Content-Length'] = str(len(json_bytes))
        
        # Отправляем запрос
        response = requests.post(
            url,
            headers=headers_final,
            data=json_bytes,
            timeout=30
        )
        
        response.encoding = 'utf-8'
        
        # Проверяем статус ответа
        if response.status_code != 200:
            logger.error(f"OpenRouter API вернул статус {response.status_code}: {response.text[:200]}")
            return None
        
        # Парсим JSON ответа
        try:
            result = response.json()
        except Exception as e:
            logger.error(f"Ошибка парсинга JSON ответа: {str(e)}")
            try:
                result = json.loads(response.content.decode('utf-8'))
            except Exception as e2:
                logger.error(f"Ошибка декодирования ответа: {str(e2)}")
                return None
        
        # Извлекаем ответ из API
        if 'choices' in result and len(result['choices']) > 0:
            content_raw = result['choices'][0]['message']['content']
            if isinstance(content_raw, bytes):
                content = content_raw.decode('utf-8')
            else:
                content = str(content_raw)
            
            # Парсим JSON из ответа
            import re
            # Убираем markdown код блоки если есть
            content_cleaned = content.replace('```json', '').replace('```', '').strip()
            
            # Ищем JSON объект
            start_idx = content_cleaned.find('{')
            end_idx = content_cleaned.rfind('}')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_str = content_cleaned[start_idx:end_idx+1]
                try:
                    dish_data = json.loads(json_str)
                    
                    # Валидация и округление данных
                    nutrition_data = {
                        "name": str(dish_data.get("name", food_name)).strip(),
                        "weight": max(1, int(float(dish_data.get("weight", weight_grams)))),
                        "calories": max(0, int(float(dish_data.get("calories", 0)))),
                        "proteins": round(max(0, float(dish_data.get("proteins", 0))), 2),
                        "fats": round(max(0, float(dish_data.get("fats", 0))), 2),
                        "carbohydrates": round(max(0, float(dish_data.get("carbohydrates", 0))), 2),
                    }
                    
                    return nutrition_data
                except json.JSONDecodeError as e:
                    logger.error(f"Ошибка парсинга JSON из ответа: {str(e)}, content: {content_cleaned[:200]}")
                    return None
        
        logger.error("Неожиданный формат ответа от OpenRouter API")
        logger.error(f"Ответ API: {result if 'result' in locals() else 'N/A'}")
        return None
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при обращении к OpenRouter API: {str(e)}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка при поиске КБЖУ: {str(e)}", exc_info=True)
        return None


def auto_calculate_goals(weight, height, age, activity_level, gender='male', goal='maintain'):
    """
    Автоматический расчёт целей КБЖУ на основе параметров пользователя
    
    Args:
        weight: вес в кг
        height: рост в см
        age: возраст в годах
        activity_level: уровень активности
        gender: пол ('male' или 'female')
        goal: цель ('lose' - похудение, 'maintain' - поддержание, 'gain' - набор)
    
    Returns:
        dict с ключами 'calories', 'proteins', 'fats', 'carbohydrates'
    """
    # Рассчитываем BMR
    bmr = calculate_bmr(weight, height, age, gender)
    
    # Рассчитываем TDEE
    tdee = calculate_tdee(bmr, activity_level)
    
    # Корректируем калории в зависимости от цели
    if goal == 'lose':
        # Дефицит 20% для похудения
        calories = tdee * 0.8
    elif goal == 'gain':
        # Профицит 10% для набора массы
        calories = tdee * 1.1
    else:
        # Поддержание текущего веса
        calories = tdee
    
    # Округляем до целого
    calories = int(round(calories))
    
    # Рассчитываем макронутриенты с учётом веса для более точного расчёта белков
    macros = calculate_macros(calories, weight=weight)
    
    return {
        'calories': calories,
        'proteins': macros['proteins'],
        'fats': macros['fats'],
        'carbohydrates': macros['carbohydrates'],
    }

