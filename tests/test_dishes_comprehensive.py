"""
Тесты для управления блюдами (Раздел 3 чек-листа)
Покрытие всех пунктов 3.1-3.6
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from rest_framework import status
from core.models import Dish, Meal


@pytest.mark.django_db
class TestDishCreate:
    """3.1. Создание блюда (POST /api/dishes/)"""

    def test_create_minimal_fields(self, authenticated_client):
        """Создание блюда с обязательными полями"""
        client = authenticated_client
        payload = {
            "name": "Овсянка",
            "date": date.today().isoformat(),
            "meal_type": "breakfast"
        }
        resp = client.post("/api/dishes/", payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["name"] == "Овсянка"
        assert resp.data["weight"] == 1  # значение по умолчанию
        assert resp.data["calories"] == 0

    def test_create_all_fields(self, authenticated_client):
        client = authenticated_client
        payload = {
            "name": "Курица",
            "date": date.today().isoformat(),
            "meal_type": "lunch",
            "weight": 200,
            "calories": 300,
            "proteins": 25.5,
            "fats": 10.0,
            "carbohydrates": 15.0,
        }
        resp = client.post("/api/dishes/", payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["weight"] == 200
        assert resp.data["calories"] == 300

    def test_create_missing_name(self, authenticated_client):
        client = authenticated_client
        payload = {
            "date": date.today().isoformat(),
            "meal_type": "dinner",
        }
        resp = client.post("/api/dishes/", payload, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_invalid_meal_type(self, authenticated_client):
        client = authenticated_client
        payload = {
            "name": "Суп",
            "date": date.today().isoformat(),
            "meal_type": "invalid",
        }
        resp = client.post("/api/dishes/", payload, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_weight_zero(self, authenticated_client):
        client = authenticated_client
        payload = {
            "name": "Творог",
            "date": date.today().isoformat(),
            "meal_type": "breakfast",
            "weight": 0,
        }
        resp = client.post("/api/dishes/", payload, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_only_user_dishes(self, authenticated_client, user, user2):
        client = authenticated_client
        # блюдо текущего пользователя
        Dish.objects.create(
            user=user,
            meal=Meal.objects.create(user=user, date=date.today(), meal_type="breakfast"),
            name="Моё блюдо",
            weight=100,
            calories=120,
            proteins=Decimal("10.00"),
            fats=Decimal("5.00"),
            carbohydrates=Decimal("12.00"),
        )
        # блюдо другого пользователя
        Dish.objects.create(
            user=user2,
            meal=Meal.objects.create(user=user2, date=date.today(), meal_type="breakfast"),
            name="Чужое блюдо",
            weight=100,
            calories=120,
            proteins=Decimal("10.00"),
            fats=Decimal("5.00"),
            carbohydrates=Decimal("12.00"),
        )
        resp = client.get("/api/dishes/")
        assert resp.status_code == status.HTTP_200_OK
        names = [item["name"] for item in resp.data["results"]]
        assert "Моё блюдо" in names
        assert "Чужое блюдо" not in names

    def test_list_filter_by_date(self, authenticated_client, user):
        client = authenticated_client
        today = date.today()
        yesterday = today - timedelta(days=1)
        Dish.objects.create(
            user=user,
            meal=Meal.objects.create(user=user, date=today, meal_type="breakfast"),
            name="Сегодня",
            weight=100,
            calories=100,
            proteins=Decimal("10.00"),
            fats=Decimal("5.00"),
            carbohydrates=Decimal("12.00"),
        )
        Dish.objects.create(
            user=user,
            meal=Meal.objects.create(user=user, date=yesterday, meal_type="breakfast"),
            name="Вчера",
            weight=100,
            calories=100,
            proteins=Decimal("10.00"),
            fats=Decimal("5.00"),
            carbohydrates=Decimal("12.00"),
        )
        resp = client.get(f"/api/dishes/?date={today.isoformat()}")
        assert resp.status_code == status.HTTP_200_OK
        names = [item["name"] for item in resp.data["results"]]
        assert "Сегодня" in names
        assert "Вчера" not in names

    def test_retrieve_own_dish(self, authenticated_client, user):
        client = authenticated_client
        dish = Dish.objects.create(
            user=user,
            meal=Meal.objects.create(user=user, date=date.today(), meal_type="lunch"),
            name="Стейк",
            weight=200,
            calories=400,
            proteins=Decimal("30.00"),
            fats=Decimal("20.00"),
            carbohydrates=Decimal("10.00"),
        )
        resp = client.get(f"/api/dishes/{dish.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["name"] == "Стейк"

    def test_retrieve_other_user_dish_forbidden(self, authenticated_client, user2):
        client = authenticated_client
        other_dish = Dish.objects.create(
            user=user2,
            meal=Meal.objects.create(user=user2, date=date.today(), meal_type="lunch"),
            name="Чужой стейк",
            weight=200,
            calories=400,
            proteins=Decimal("30.00"),
            fats=Decimal("20.00"),
            carbohydrates=Decimal("10.00"),
        )
        resp = client.get(f"/api/dishes/{other_dish.id}/")
        assert resp.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]

    def test_update_name(self, authenticated_client, user):
        client = authenticated_client
        dish = Dish.objects.create(
            user=user,
            meal=Meal.objects.create(user=user, date=date.today(), meal_type="dinner"),
            name="Старое имя",
            weight=150,
            calories=200,
            proteins=Decimal("15.00"),
            fats=Decimal("10.00"),
            carbohydrates=Decimal("20.00"),
        )
        resp = client.patch(f"/api/dishes/{dish.id}/", {"name": "Новое имя"}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["name"] == "Новое имя"

    def test_update_negative_calories(self, authenticated_client, user):
        client = authenticated_client
        dish = Dish.objects.create(
            user=user,
            meal=Meal.objects.create(user=user, date=date.today(), meal_type="dinner"),
            name="Тест",
            weight=150,
            calories=200,
            proteins=Decimal("15.00"),
            fats=Decimal("10.00"),
            carbohydrates=Decimal("20.00"),
        )
        resp = client.patch(f"/api/dishes/{dish.id}/", {"calories": -1}, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_delete_dish(self, authenticated_client, user):
        client = authenticated_client
        dish = Dish.objects.create(
            user=user,
            meal=Meal.objects.create(user=user, date=date.today(), meal_type="snack"),
            name="Удалить",
            weight=50,
            calories=100,
            proteins=Decimal("5.00"),
            fats=Decimal("3.00"),
            carbohydrates=Decimal("10.00"),
        )
        resp = client.delete(f"/api/dishes/{dish.id}/")
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        assert not Dish.objects.filter(id=dish.id).exists()

