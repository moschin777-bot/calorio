from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from core.throttles import RegistrationThrottle, LoginThrottle
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    ProfileSerializer,
    ProfileRetrieveSerializer,
    ProfileUpdateSerializer,
    EmailUpdateSerializer,
    PasswordChangeSerializer
)
from .models import Profile

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """API для регистрации нового пользователя"""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [RegistrationThrottle]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Генерируем токены для нового пользователя
        refresh = RefreshToken.for_user(user)
        
        # Получаем профиль для first_name (должен быть создан в сериализаторе)
        profile, _ = Profile.objects.get_or_create(user=user)
        
        return Response({
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': profile.first_name,
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    """API для входа пользователя с защитой от timing attacks"""
    serializer_class = UserLoginSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [LoginThrottle]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        # Защита от timing attacks: всегда выполняем проверку пароля
        # даже если пользователь не найден
        
        # Пытаемся найти пользователя по email
        try:
            user = User.objects.get(email=email)
            username = user.username
            user_exists = True
        except User.DoesNotExist:
            user_exists = False
            # Создаём фиктивный username для выравнивания времени
            # (authenticate всегда выполняет проверку пароля)
            username = email.split('@')[0] if '@' in email else email
        
        # Всегда выполняем authenticate() для защиты от timing attacks
        # authenticate() всегда проверяет пароль, даже если пользователь не найден
        authenticated_user = authenticate(
            request=request,
            username=username,
            password=password
        )
        
        # Проверяем результат
        if not user_exists or authenticated_user is None:
            # Возвращаем одинаковое сообщение независимо от причины
            return Response({
                'detail': 'Неверный email или пароль.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        user = authenticated_user
        
        if not user.is_active:
            return Response({
                'detail': 'Аккаунт деактивирован.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Генерируем токены
        refresh = RefreshToken.for_user(user)
        
        # Получаем профиль для first_name
        profile, _ = Profile.objects.get_or_create(user=user)
        
        return Response({
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': profile.first_name,
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)


class LogoutView(generics.GenericAPIView):
    """API для выхода пользователя
    
    Согласно документации API:
    - Требует аутентификации
    - Принимает refresh token в теле запроса
    - Добавляет токен в чёрный список
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response({
                    'detail': 'Токен обновления не предоставлен.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response({
                'detail': 'Успешный выход из системы.'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'detail': 'Неверный токен.'
            }, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(generics.RetrieveUpdateAPIView):
    """API для получения и обновления профиля пользователя"""
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        """Возвращаем разные сериализаторы для GET и PATCH/PUT"""
        if self.request.method in ['PATCH', 'PUT']:
            return ProfileUpdateSerializer
        return ProfileRetrieveSerializer

    def get_object(self):
        """Возвращает профиль для обновления или данные для получения"""
        if self.request.method in ['PATCH', 'PUT']:
            # Для обновления возвращаем объект Profile
            profile, created = Profile.objects.get_or_create(user=self.request.user)
            return profile
        else:
            # Для получения возвращаем объект Profile (сериализатор сам извлечёт нужные поля)
            profile, created = Profile.objects.get_or_create(user=self.request.user)
            return profile

    def retrieve(self, request, *args, **kwargs):
        """Получение профиля пользователя (только id, email, first_name)"""
        profile = self.get_object()
        return Response({
            'id': request.user.id,
            'email': request.user.email,
            'first_name': profile.first_name or ''
        })

    def update(self, request, *args, **kwargs):
        """Обновление профиля"""
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, 
            data=request.data, 
            partial=partial,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Обновляем пользователя из БД, чтобы получить актуальные данные
        request.user.refresh_from_db()
        profile, _ = Profile.objects.get_or_create(user=request.user)
        profile.refresh_from_db()
        
        return Response({
            'id': request.user.id,
            'email': request.user.email,
            'first_name': profile.first_name or ''
        }, status=status.HTTP_200_OK)


class EmailUpdateView(generics.GenericAPIView):
    """API для обновления email пользователя"""
    serializer_class = EmailUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.email = serializer.validated_data['email']
        user.save()
        
        return Response({
            'message': 'Email успешно обновлён.',
            'email': user.email
        }, status=status.HTTP_200_OK)


class PasswordChangeView(generics.GenericAPIView):
    """API для смены пароля пользователя"""
    serializer_class = PasswordChangeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        # Инвалидируем все существующие токены пользователя при смене пароля
        # Это защищает от использования украденных токенов
        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
        from rest_framework_simplejwt.tokens import RefreshToken
        
        # Получаем все outstanding токены пользователя
        outstanding_tokens = OutstandingToken.objects.filter(user=user)
        for token in outstanding_tokens:
            try:
                refresh_token = RefreshToken(token.token)
                refresh_token.blacklist()
            except Exception:
                # Токен уже истёк или невалиден, пропускаем
                pass
        
        return Response({
            'detail': 'Пароль успешно изменён.'
        }, status=status.HTTP_200_OK)
