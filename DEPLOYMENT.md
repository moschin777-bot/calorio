# Руководство по деплою Calorio API

Это руководство описывает процесс деплоя Calorio API на production сервер.

## Содержание

1. [Подготовка к деплою](#подготовка-к-деплою)
2. [Деплой на VPS (Ubuntu)](#деплой-на-vps-ubuntu)
3. [Деплой с Docker](#деплой-с-docker)
4. [Деплой на AWS](#деплой-на-aws)
5. [Деплой на Heroku](#деплой-на-heroku)
6. [Post-deployment проверки](#post-deployment-проверки)
7. [Мониторинг и обслуживание](#мониторинг-и-обслуживание)

## Подготовка к деплою

### 1. Чек-лист перед деплоем

- [ ] Все тесты проходят успешно
- [ ] Покрытие кода тестами > 80%
- [ ] Линтеры не выдают критических ошибок
- [ ] Все миграции созданы и протестированы
- [ ] Переменные окружения настроены
- [ ] SECRET_KEY сгенерирован для production
- [ ] DEBUG=False
- [ ] ALLOWED_HOSTS настроен
- [ ] CORS_ALLOWED_ORIGINS настроен
- [ ] SSL сертификат получен
- [ ] Бэкап базы данных создан
- [ ] Rollback план подготовлен

### 2. Генерация секретных ключей

```bash
# SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# PAYMENT_WEBHOOK_SECRET
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Настройка переменных окружения

Создайте файл `.env` на production сервере:

```env
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=api.calorio.app,www.calorio.app
CORS_ALLOWED_ORIGINS=https://calorio.app,https://www.calorio.app

DATABASE_URL=postgresql://user:password@localhost:5432/calorio

OPENROUTER_API_KEY=your-openrouter-api-key
PAYMENT_WEBHOOK_SECRET=your-webhook-secret

SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

## Деплой на VPS (Ubuntu)

### 1. Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка зависимостей
sudo apt install -y python3.11 python3.11-venv python3-pip postgresql postgresql-contrib nginx git

# Установка Redis (опционально)
sudo apt install -y redis-server
```

### 2. Настройка PostgreSQL

```bash
# Вход в PostgreSQL
sudo -u postgres psql

# Создание базы данных и пользователя
CREATE DATABASE calorio;
CREATE USER calorio_user WITH PASSWORD 'your-strong-password';
ALTER ROLE calorio_user SET client_encoding TO 'utf8';
ALTER ROLE calorio_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE calorio_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE calorio TO calorio_user;
\q
```

### 3. Клонирование проекта

```bash
# Создание директории для проекта
sudo mkdir -p /var/www/calorio
sudo chown $USER:$USER /var/www/calorio

# Клонирование репозитория
cd /var/www/calorio
git clone https://github.com/yourusername/calorio.git .
```

### 4. Настройка виртуального окружения

```bash
# Создание виртуального окружения
python3.11 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Настройка приложения

```bash
# Создание .env файла
nano .env
# Вставьте переменные окружения

# Применение миграций
python manage.py migrate

# Сбор статических файлов
python manage.py collectstatic --noinput

# Создание суперпользователя
python manage.py createsuperuser
```

### 6. Настройка Gunicorn

Создайте systemd service файл:

```bash
sudo nano /etc/systemd/system/calorio.service
```

Содержимое файла:

```ini
[Unit]
Description=Calorio API
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/calorio
Environment="PATH=/var/www/calorio/venv/bin"
EnvironmentFile=/var/www/calorio/.env
ExecStart=/var/www/calorio/venv/bin/gunicorn --workers 4 --bind unix:/var/www/calorio/calorio.sock calorio_api.wsgi:application

[Install]
WantedBy=multi-user.target
```

Запуск сервиса:

```bash
sudo systemctl start calorio
sudo systemctl enable calorio
sudo systemctl status calorio
```

### 7. Настройка Nginx

Создайте конфигурацию Nginx:

```bash
sudo nano /etc/nginx/sites-available/calorio
```

Содержимое файла:

```nginx
server {
    listen 80;
    server_name api.calorio.app;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias /var/www/calorio/staticfiles/;
    }
    
    location /media/ {
        alias /var/www/calorio/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/calorio/calorio.sock;
    }
}
```

Активация конфигурации:

```bash
sudo ln -s /etc/nginx/sites-available/calorio /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

### 8. Настройка SSL (Let's Encrypt)

```bash
# Установка Certbot
sudo apt install -y certbot python3-certbot-nginx

# Получение SSL сертификата
sudo certbot --nginx -d api.calorio.app

# Автоматическое обновление сертификата
sudo certbot renew --dry-run
```

## Деплой с Docker

### 1. Установка Docker и Docker Compose

```bash
# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установка Docker Compose
sudo apt install -y docker-compose

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER
```

### 2. Клонирование проекта

```bash
git clone https://github.com/yourusername/calorio.git
cd calorio
```

### 3. Настройка переменных окружения

```bash
cp .env.example .env
nano .env
# Отредактируйте переменные для production
```

### 4. Запуск контейнеров

```bash
# Сборка и запуск
docker-compose up -d --build

# Применение миграций
docker-compose exec web python manage.py migrate

# Сбор статических файлов
docker-compose exec web python manage.py collectstatic --noinput

# Создание суперпользователя
docker-compose exec web python manage.py createsuperuser
```

### 5. Проверка работы

```bash
# Просмотр логов
docker-compose logs -f web

# Проверка статуса контейнеров
docker-compose ps
```

## Деплой на AWS

### 1. Использование AWS Elastic Beanstalk

```bash
# Установка EB CLI
pip install awsebcli

# Инициализация
eb init -p python-3.11 calorio-api

# Создание окружения
eb create calorio-production

# Деплой
eb deploy
```

### 2. Настройка переменных окружения в AWS

```bash
eb setenv SECRET_KEY=your-secret-key DEBUG=False ALLOWED_HOSTS=your-domain.com
```

### 3. Настройка RDS (PostgreSQL)

1. Создайте RDS инстанс через AWS Console
2. Настройте Security Group для доступа
3. Добавьте DATABASE_URL в переменные окружения

## Деплой на Heroku

### 1. Подготовка

```bash
# Установка Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# Вход в Heroku
heroku login
```

### 2. Создание приложения

```bash
# Создание приложения
heroku create calorio-api

# Добавление PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Добавление Redis
heroku addons:create heroku-redis:hobby-dev
```

### 3. Настройка переменных окружения

```bash
heroku config:set SECRET_KEY=your-secret-key
heroku config:set DEBUG=False
heroku config:set ALLOWED_HOSTS=calorio-api.herokuapp.com
```

### 4. Деплой

```bash
# Деплой через Git
git push heroku main

# Применение миграций
heroku run python manage.py migrate

# Создание суперпользователя
heroku run python manage.py createsuperuser
```

## Post-deployment проверки

### 1. Smoke Tests

```bash
# Health check
curl https://api.calorio.app/api/health/

# Swagger документация
curl https://api.calorio.app/api/docs/

# Регистрация пользователя
curl -X POST https://api.calorio.app/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123","first_name":"Test"}'
```

### 2. Проверка логов

```bash
# Docker
docker-compose logs -f web

# Systemd
sudo journalctl -u calorio -f

# Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 3. Проверка производительности

```bash
# Установка Apache Bench
sudo apt install -y apache2-utils

# Нагрузочное тестирование
ab -n 1000 -c 10 https://api.calorio.app/api/health/
```

## Мониторинг и обслуживание

### 1. Настройка мониторинга

- Настройте Sentry для отслеживания ошибок
- Настройте Datadog/CloudWatch для метрик
- Настройте UptimeRobot для мониторинга доступности

### 2. Бэкапы

```bash
# Автоматический бэкап PostgreSQL
# Добавьте в crontab
0 2 * * * pg_dump -U calorio_user calorio > /backups/calorio_$(date +\%Y\%m\%d).sql
```

### 3. Обновление приложения

```bash
# Pull последних изменений
git pull origin main

# Применение миграций
python manage.py migrate

# Сбор статических файлов
python manage.py collectstatic --noinput

# Перезапуск сервиса
sudo systemctl restart calorio
```

### 4. Rollback

```bash
# Откат к предыдущей версии
git checkout <previous-commit>

# Откат миграций
python manage.py migrate <app_name> <previous_migration>

# Перезапуск сервиса
sudo systemctl restart calorio
```

## Troubleshooting

### Проблема: 502 Bad Gateway

```bash
# Проверка статуса Gunicorn
sudo systemctl status calorio

# Проверка логов
sudo journalctl -u calorio -n 50
```

### Проблема: Медленные запросы

```bash
# Проверка медленных запросов в PostgreSQL
# Включите логирование медленных запросов в postgresql.conf
log_min_duration_statement = 1000
```

### Проблема: Недостаточно памяти

```bash
# Проверка использования памяти
free -h

# Уменьшение количества Gunicorn workers
# Отредактируйте /etc/systemd/system/calorio.service
--workers 2
```

## Контакты и поддержка

- Email: support@calorio.app
- Documentation: https://docs.calorio.app
- GitHub Issues: https://github.com/yourusername/calorio/issues

