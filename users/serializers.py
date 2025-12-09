from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Profile

User = get_user_model()


class UserRegistrationSerializer(serializers.Serializer):
    """Сериализатор для регистрации пользователя
    
    Согласно документации API:
    - first_name: обязательно, 1-150 символов
    - email: обязательно, валидный email, уникальный
    - password: обязательно, минимум 8 символов
    """
    first_name = serializers.CharField(
        required=True,
        max_length=150,
        min_length=1,
        allow_blank=False
    )
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8
    )

    def validate_first_name(self, value):
        """Валидация имени"""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError(["Это поле обязательно."])
        if len(value) > 150:
            raise serializers.ValidationError(["Убедитесь, что это значение содержит не более 150 символов."])
        return value.strip()

    def validate_email(self, value):
        """Валидация email: должен быть уникальным"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(["Пользователь с таким email уже существует."])
        return value.lower()

    def validate_password(self, value):
        """Валидация пароля"""
        if len(value) < 8:
            raise serializers.ValidationError(["Пароль должен содержать минимум 8 символов."])
        return value

    def create(self, validated_data):
        """Создание пользователя и профиля"""
        email = validated_data['email']
        password = validated_data['password']
        first_name = validated_data['first_name']
        
        # Создаём username из email (до @)
        username = email.split('@')[0]
        # Если такой username уже существует, добавляем случайные цифры
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Создаём пользователя
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        # Создаём профиль с именем
        Profile.objects.create(user=user, first_name=first_name)
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """Сериализатор для входа пользователя
    
    Согласно документации API:
    - email: обязательно, валидный email
    - password: обязательно
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class ProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для профиля пользователя"""
    email = serializers.EmailField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Profile
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'age', 'weight', 'height', 'activity_level',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class ProfileRetrieveSerializer(serializers.Serializer):
    """Сериализатор для получения профиля (только id, email, first_name)
    
    Примечание: Этот сериализатор используется только для определения структуры ответа.
    Фактический ответ формируется в views.
    """
    id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(read_only=True)
    first_name = serializers.CharField(read_only=True, allow_blank=True)


class ProfileUpdateSerializer(serializers.Serializer):
    """Сериализатор для обновления профиля (только first_name и email)"""
    first_name = serializers.CharField(
        required=False,
        max_length=150,
        allow_blank=False,
        allow_null=False
    )
    email = serializers.EmailField(required=False)

    def validate_first_name(self, value):
        """Валидация имени: если передано, должно быть 1-150 символов"""
        if value is not None and value != '':
            value = value.strip()
            if len(value) == 0:
                raise serializers.ValidationError(["Это поле обязательно."])
            if len(value) > 150:
                raise serializers.ValidationError(["Убедитесь, что это значение содержит не более 150 символов."])
        elif value == '':
            # Пустая строка недопустима, если поле передано
            raise serializers.ValidationError(["Это поле обязательно."])
        return value

    def validate_email(self, value):
        """Валидация email: должен быть валидным и уникальным"""
        if value:
            # Проверка уникальности
            User = get_user_model()
            user = self.context['request'].user
            if User.objects.filter(email=value).exclude(pk=user.pk).exists():
                raise serializers.ValidationError(["Пользователь с таким email уже существует."])
        return value

    def update(self, instance, validated_data):
        """Обновление профиля и email пользователя"""
        user = instance.user
        
        # Обновляем first_name в профиле (только если передано)
        if 'first_name' in validated_data:
            instance.first_name = validated_data['first_name']
            instance.save()
        
        # Обновляем email в пользователе (только если передано)
        if 'email' in validated_data:
            user.email = validated_data['email']
            user.save()
        
        return instance


class EmailUpdateSerializer(serializers.Serializer):
    """Сериализатор для обновления email"""
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        User = get_user_model()
        if User.objects.filter(email=value).exclude(pk=self.context['request'].user.pk).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует.")
        return value


class PasswordChangeSerializer(serializers.Serializer):
    """Сериализатор для смены пароля"""
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=8
    )

    def validate_new_password(self, value):
        """Валидация нового пароля"""
        if len(value) < 8:
            raise serializers.ValidationError(["Пароль должен содержать минимум 8 символов."])
        
        # Используем стандартные валидаторы Django
        user = self.context['request'].user
        try:
            validate_password(value, user)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        
        return value

    def validate(self, attrs):
        """Проверка, что новый пароль отличается от старого"""
        old_password = attrs.get('old_password')
        new_password = attrs.get('new_password')
        
        user = self.context['request'].user
        
        # Проверяем старый пароль
        if not user.check_password(old_password):
            raise serializers.ValidationError({
                "old_password": ["Неверный пароль."]
            })
        
        # Проверяем, что новый пароль отличается от старого
        if user.check_password(new_password):
            raise serializers.ValidationError({
                "new_password": ["Новый пароль должен отличаться от старого."]
            })
        
        return attrs

