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

