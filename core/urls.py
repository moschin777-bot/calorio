from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DishViewSet

app_name = 'core'

router = DefaultRouter()
router.register(r'v1/dishes', DishViewSet, basename='dish')

urlpatterns = [
    path('', include(router.urls)),
]

