#!/bin/bash
set -e

echo "Starting entrypoint script..."

# Ожидание доступности базы данных (если используется PostgreSQL)
if [ -n "$DATABASE_URL" ]; then
    echo "Waiting for database..."
    until pg_isready -h $(echo $DATABASE_URL | sed -n 's/.*@\(.*\):.*/\1/p') 2>/dev/null; do
        echo "Database is unavailable - sleeping"
        sleep 2
    done
    echo "Database is up!"
fi

# Создание директории для логов, если не существует
mkdir -p /app/logs

# Применение миграций
echo "Applying database migrations..."
python manage.py migrate --noinput

# Сбор статических файлов
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Создание суперпользователя (если переменные окружения установлены)
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "Creating superuser..."
    python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='$DJANGO_SUPERUSER_EMAIL').exists():
    User.objects.create_superuser('$DJANGO_SUPERUSER_EMAIL', '$DJANGO_SUPERUSER_PASSWORD', first_name='Admin')
    print('Superuser created successfully')
else:
    print('Superuser already exists')
END
fi

echo "Starting application..."
exec "$@"

