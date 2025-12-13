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


# Локальная база данных популярных блюд (fallback если OpenRouter недоступен)
# Значения на 100г продукта
FOOD_DATABASE = {
    # Яичные блюда
    "яичница": {"calories_per_100g": 200, "proteins_per_100g": 13, "fats_per_100g": 15, "carbs_per_100g": 1},
    "яичница с помидорами": {"calories_per_100g": 180, "proteins_per_100g": 12, "fats_per_100g": 13, "carbs_per_100g": 3},
    "омлет": {"calories_per_100g": 190, "proteins_per_100g": 12, "fats_per_100g": 14, "carbs_per_100g": 2},
    "омлет с беконом": {"calories_per_100g": 250, "proteins_per_100g": 15, "fats_per_100g": 18, "carbs_per_100g": 3},
    
    # Супы
    "суп гороховый": {"calories_per_100g": 60, "proteins_per_100g": 4, "fats_per_100g": 2, "carbs_per_100g": 8},
    "гороховый суп": {"calories_per_100g": 60, "proteins_per_100g": 4, "fats_per_100g": 2, "carbs_per_100g": 8},
    "борщ": {"calories_per_100g": 50, "proteins_per_100g": 2, "fats_per_100g": 2, "carbs_per_100g": 6},
    "щи": {"calories_per_100g": 45, "proteins_per_100g": 2, "fats_per_100g": 2, "carbs_per_100g": 5},
    
    # Сырники и десерты
    "сырники": {"calories_per_100g": 250, "proteins_per_100g": 12, "fats_per_100g": 10, "carbs_per_100g": 25},
    "сырник": {"calories_per_100g": 250, "proteins_per_100g": 12, "fats_per_100g": 10, "carbs_per_100g": 25},
    "варенье": {"calories_per_100g": 250, "proteins_per_100g": 0, "fats_per_100g": 0, "carbs_per_100g": 65},
    
    # Каши
    "гречка": {"calories_per_100g": 100, "proteins_per_100g": 4, "fats_per_100g": 1, "carbs_per_100g": 20},
    "гречневая каша": {"calories_per_100g": 100, "proteins_per_100g": 4, "fats_per_100g": 1, "carbs_per_100g": 20},
    "манка": {"calories_per_100g": 80, "proteins_per_100g": 3, "fats_per_100g": 1, "carbs_per_100g": 15},
    "манка с вареньем": {"calories_per_100g": 120, "proteins_per_100g": 2, "fats_per_100g": 1, "carbs_per_100g": 25},
    "овсянка": {"calories_per_100g": 90, "proteins_per_100g": 3, "fats_per_100g": 2, "carbs_per_100g": 15},
    "рис": {"calories_per_100g": 130, "proteins_per_100g": 3, "fats_per_100g": 0, "carbs_per_100g": 28},
    
    # Мясные блюда
    "котлеты": {"calories_per_100g": 250, "proteins_per_100g": 18, "fats_per_100g": 15, "carbs_per_100g": 10},
    "котлета": {"calories_per_100g": 250, "proteins_per_100g": 18, "fats_per_100g": 15, "carbs_per_100g": 10},
    "гречка с котлетами": {"calories_per_100g": 175, "proteins_per_100g": 11, "fats_per_100g": 8, "carbs_per_100g": 15},
    "рис с котлетами": {"calories_per_100g": 190, "proteins_per_100g": 11, "fats_per_100g": 8, "carbs_per_100g": 18},
    
    # Выпечка
    "ватрушка": {"calories_per_100g": 300, "proteins_per_100g": 8, "fats_per_100g": 12, "carbs_per_100g": 45},
    "ватрушки": {"calories_per_100g": 300, "proteins_per_100g": 8, "fats_per_100g": 12, "carbs_per_100g": 45},
}

def _search_local_database(food_name, weight_grams):
    """Поиск в локальной базе данных"""
    food_lower = food_name.lower().strip()
    
    # Прямое совпадение
    if food_lower in FOOD_DATABASE:
        data = FOOD_DATABASE[food_lower]
        ratio = weight_grams / 100.0
        return {
            "name": food_name,
            "weight": weight_grams,
            "calories": int(round(data["calories_per_100g"] * ratio)),
            "proteins": round(data["proteins_per_100g"] * ratio, 2),
            "fats": round(data["fats_per_100g"] * ratio, 2),
            "carbohydrates": round(data["carbs_per_100g"] * ratio, 2),
        }
    
    # Поиск по частичному совпадению
    for key, data in FOOD_DATABASE.items():
        if key in food_lower or food_lower in key:
            ratio = weight_grams / 100.0
            return {
                "name": food_name,
                "weight": weight_grams,
                "calories": int(round(data["calories_per_100g"] * ratio)),
                "proteins": round(data["proteins_per_100g"] * ratio, 2),
                "fats": round(data["fats_per_100g"] * ratio, 2),
                "carbohydrates": round(data["carbs_per_100g"] * ratio, 2),
            }
    
    return None

def search_food_nutrition(food_name, weight_grams=100):
    """
    Поиск КБЖУ по названию продукта через OpenRouter API (LLM) с fallback на локальную базу.
    
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
    
    # Сначала пробуем локальную базу данных
    local_result = _search_local_database(food_name, weight_grams)
    if local_result:
        logger.info(f"Найдено в локальной базе: {food_name}")
        return local_result
    
    # Получаем API ключ из настроек
    api_key = getattr(settings, 'OPENROUTER_API_KEY', '')
    
    if not api_key:
        logger.warning("OpenRouter API ключ не настроен, используем только локальную базу")
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
        prompt = f"""Определи пищевую ценность (КБЖУ) для блюда: {food_name}, вес {weight_grams}г.

Верни ТОЛЬКО JSON:
{{
  "name": "название на русском",
  "weight": {weight_grams},
  "calories": число,
  "proteins": число,
  "fats": число,
  "carbohydrates": число
}}

Используй реалистичные значения для указанного веса."""
        
        payload = {
            "model": "openai/gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 300,
            "temperature": 0.1,
        }
        
        logger.info(f"Отправка запроса к OpenRouter для: {food_name}")
        
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
            error_text = response.text[:200] if hasattr(response, 'text') else "Не удалось прочитать ответ"
            logger.error(f"OpenRouter API вернул статус {response.status_code}: {error_text}")
            
            # Если ошибка 402 (недостаточно кредитов), пробуем локальную базу
            if response.status_code == 402:
                logger.warning("OpenRouter API: недостаточно кредитов, пробуем локальную базу")
                return _search_local_database(food_name, weight_grams)
            
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
        logger.error(f"Ответ API (первые 500 символов): {str(result)[:500] if 'result' in locals() else 'N/A'}")
        if 'result' in locals() and isinstance(result, dict):
            logger.error(f"Ключи в ответе: {list(result.keys())}")
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

