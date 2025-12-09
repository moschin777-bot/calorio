from rest_framework import serializers
from .models import Dish, DailyGoal, Meal
from django.utils.dateparse import parse_date
from .utils import auto_calculate_goals


class DishSerializer(serializers.ModelSerializer):
    """Сериализатор для блюда"""
    date = serializers.DateField(
        format='%Y-%m-%d', 
        input_formats=['%Y-%m-%d'], 
        write_only=True,
        required=True
    )
    meal_type = serializers.ChoiceField(
        choices=Meal.MEAL_TYPE_CHOICES,
        write_only=True,
        required=True
    )
    weight = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    calories = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    proteins = serializers.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        required=False, 
        allow_null=True,
        min_value=0
    )
    fats = serializers.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        required=False, 
        allow_null=True,
        min_value=0
    )
    carbohydrates = serializers.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        required=False, 
        allow_null=True,
        min_value=0
    )
    
    class Meta:
        model = Dish
        fields = (
            'id', 'name', 'weight', 'calories', 'proteins', 'fats', 
            'carbohydrates', 'date', 'meal_type', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
        extra_kwargs = {
            'name': {'required': True}
        }
    
    def validate_meal_type(self, value):
        """Валидация типа приёма пищи"""
        valid_types = [choice[0] for choice in Meal.MEAL_TYPE_CHOICES]
        if value not in valid_types:
            raise serializers.ValidationError(
                f"Выберите правильный вариант. Варианты: {', '.join(valid_types)}."
            )
        return value
    
    def validate_date(self, value):
        """Валидация даты"""
        if value is None:
            raise serializers.ValidationError("Неверный формат даты.")
        return value
    
    def validate_weight(self, value):
        """Валидация массы"""
        if value is not None and value < 1:
            raise serializers.ValidationError("Убедитесь, что это значение больше либо равно 1.")
        return value
    
    def validate_calories(self, value):
        """Валидация калорий"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Убедитесь, что это значение больше либо равно 0.")
        return value
    
    def validate_proteins(self, value):
        """Валидация белков"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Убедитесь, что это значение больше либо равно 0.")
        return value
    
    def validate_fats(self, value):
        """Валидация жиров"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Убедитесь, что это значение больше либо равно 0.")
        return value
    
    def validate_carbohydrates(self, value):
        """Валидация углеводов"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Убедитесь, что это значение больше либо равно 0.")
        return value
    
    def to_representation(self, instance):
        """Преобразование для вывода - добавляем date и meal_type из связанного Meal"""
        representation = super().to_representation(instance)
        if instance.meal:
            representation['date'] = instance.meal.date.strftime('%Y-%m-%d')
            representation['meal_type'] = instance.meal.meal_type
        return representation


class DailyGoalSerializer(serializers.ModelSerializer):
    """Сериализатор для целей КБЖУ на день"""
    date = serializers.DateField(format='%Y-%m-%d', input_formats=['%Y-%m-%d'], read_only=True)
    
    class Meta:
        model = DailyGoal
        fields = (
            'id', 'date', 'calories', 'proteins', 'fats', 
            'carbohydrates', 'is_auto_calculated', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'date', 'is_auto_calculated', 'created_at', 'updated_at')
    
    def validate_calories(self, value):
        """Валидация калорий"""
        if value < 1:
            raise serializers.ValidationError("Убедитесь, что это значение больше либо равно 1.")
        return value
    
    def validate_proteins(self, value):
        """Валидация белков"""
        if value < 0:
            raise serializers.ValidationError("Убедитесь, что это значение больше либо равно 0.")
        return value
    
    def validate_fats(self, value):
        """Валидация жиров"""
        if value < 0:
            raise serializers.ValidationError("Убедитесь, что это значение больше либо равно 0.")
        return value
    
    def validate_carbohydrates(self, value):
        """Валидация углеводов"""
        if value < 0:
            raise serializers.ValidationError("Убедитесь, что это значение больше либо равно 0.")
        return value


class DishRecognitionSerializer(serializers.Serializer):
    """Сериализатор для распознавания блюда по фотографии"""
    image_base64 = serializers.CharField(required=True, allow_blank=False)
    date = serializers.DateField(
        format='%Y-%m-%d',
        input_formats=['%Y-%m-%d'],
        required=False,
        help_text="Дата для блюда (по умолчанию текущая дата)"
    )
    meal_type = serializers.ChoiceField(
        choices=[
            ('breakfast', 'Завтрак'),
            ('lunch', 'Обед'),
            ('dinner', 'Ужин'),
            ('snack', 'Перекус'),
        ],
        required=False,
        help_text="Тип приёма пищи"
    )
    
    def validate_image_base64(self, value):
        """Валидация формата base64 изображения"""
        if not value:
            raise serializers.ValidationError("Изображение обязательно для распознавания.")
        
        # Проверяем, что это base64 строка
        # Может быть с префиксом data:image/...;base64, или без него
        base64_data = value
        if ',' in value:
            # Если есть префикс, извлекаем только base64 часть
            base64_data = value.split(',')[-1]
        
        # Проверяем, что это валидный base64
        import base64
        try:
            # Пробуем декодировать
            decoded = base64.b64decode(base64_data, validate=True)
            
            # Проверяем размер (максимум 10 МБ)
            max_size = 10 * 1024 * 1024  # 10 МБ в байтах
            if len(decoded) > max_size:
                raise serializers.ValidationError("Размер изображения не должен превышать 10 МБ.")
            
            # Проверяем, что это изображение (проверяем первые байты)
            from PIL import Image
            import io
            try:
                img = Image.open(io.BytesIO(decoded))
                img.verify()  # Проверяем, что это валидное изображение
            except Exception:
                raise serializers.ValidationError("Неверный формат изображения. Ожидается base64.")
            
        except base64.binascii.Error:
            raise serializers.ValidationError("Неверный формат base64.")
        except Exception as e:
            if "превышать" in str(e) or "формат" in str(e):
                raise
            raise serializers.ValidationError("Неверный формат изображения. Ожидается base64.")
        
        return value


class AutoCalculateGoalsSerializer(serializers.Serializer):
    """Сериализатор для автоматического расчёта целей КБЖУ"""
    weight = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=True,
        min_value=1,
        help_text="Вес в кг"
    )
    height = serializers.IntegerField(
        required=True,
        min_value=1,
        help_text="Рост в см"
    )
    age = serializers.IntegerField(
        required=True,
        min_value=1,
        max_value=150,
        help_text="Возраст в годах"
    )
    activity_level = serializers.ChoiceField(
        choices=[
            ('sedentary', 'Малоподвижный'),
            ('light', 'Лёгкая активность'),
            ('moderate', 'Умеренная активность'),
            ('active', 'Высокая активность'),
            ('very_active', 'Очень высокая активность'),
        ],
        required=True,
        help_text="Уровень физической активности"
    )
    gender = serializers.ChoiceField(
        choices=[('male', 'Мужской'), ('female', 'Женский')],
        default='male',
        required=False,
        help_text="Пол"
    )
    goal = serializers.ChoiceField(
        choices=[
            ('lose', 'Похудение'),
            ('maintain', 'Поддержание'),
            ('gain', 'Набор массы'),
        ],
        default='maintain',
        required=False,
        help_text="Цель"
    )
    date = serializers.DateField(
        format='%Y-%m-%d',
        input_formats=['%Y-%m-%d'],
        required=True,
        help_text="Дата для установки цели"
    )
    
    def validate_weight(self, value):
        """Валидация веса"""
        if value < 1:
            raise serializers.ValidationError("Вес должен быть больше 0.")
        return value
    
    def validate_height(self, value):
        """Валидация роста"""
        if value < 1:
            raise serializers.ValidationError("Рост должен быть больше 0.")
        return value
    
    def validate_age(self, value):
        """Валидация возраста"""
        if value < 1 or value > 150:
            raise serializers.ValidationError("Возраст должен быть от 1 до 150 лет.")
        return value

