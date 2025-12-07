from rest_framework import viewsets, permissions
from .models import Dish
from .serializers import DishSerializer


class DishViewSet(viewsets.ModelViewSet):
    """ViewSet для управления блюдами"""
    queryset = Dish.objects.all()
    serializer_class = DishSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Возвращаем только блюда текущего пользователя, если он авторизован"""
        queryset = Dish.objects.all()
        # Если нужно фильтровать по пользователю, можно раскомментировать:
        # if self.request.user.is_authenticated:
        #     queryset = queryset.filter(user=self.request.user)
        return queryset
    
    def perform_create(self, serializer):
        """При создании блюда автоматически связываем его с текущим пользователем"""
        # Если нужно автоматически устанавливать user, можно раскомментировать:
        # serializer.save(user=self.request.user)
        serializer.save()

