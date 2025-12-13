from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DishViewSet, 
    DailyGoalView, 
    DishRecognitionView,
    AutoCalculateGoalsView,
    DayDataView,
    FoodSearchView
)

app_name = 'core'

router = DefaultRouter()
router.register(r'dishes', DishViewSet, basename='dish')

urlpatterns = [
    path('days/<str:date>/', DayDataView.as_view(), name='day-data'),
    path('goals/auto-calculate/', AutoCalculateGoalsView.as_view(), name='goal-auto-calculate'),
    path('goals/<str:date>/', DailyGoalView.as_view(), name='goal-detail'),
    path('dishes/recognize/', DishRecognitionView.as_view(), name='dish-recognize'),
    path('dishes/search-nutrition/', FoodSearchView.as_view(), name='food-search'),
    path('', include(router.urls)),
]

