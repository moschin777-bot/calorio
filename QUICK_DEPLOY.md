# Быстрый деплой на colories.ru

## Шаг 1: Подключение к серверу

```bash
ssh root@217.26.29.106
# Пароль: C&6!wMqm!wOZ
```

## Шаг 2: Установка ПО (одна команда)

```bash
curl -fsSL https://raw.githubusercontent.com/yourusername/calorio/main/scripts/server_setup.sh | sudo bash
```

Или вручную:

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Python 3.11
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Установка PostgreSQL, Nginx, Certbot
sudo apt install -y postgresql postgresql-contrib libpq-dev nginx certbot python3-certbot-nginx git

# Создание пользователя
sudo useradd -m -s /bin/bash calorio

# Создание директорий
sudo mkdir -p /var/www/calorio/logs /var/www/calorio/media /var/www/calorio/staticfiles
sudo chown -R calorio:calorio /var/www/calorio

# Настройка PostgreSQL
sudo -u postgres psql <<EOF
CREATE DATABASE calorio;
CREATE USER calorio_user WITH PASSWORD 'C&6!wMqm!wOZ';
ALTER ROLE calorio_user SET client_encoding TO 'utf8';
ALTER ROLE calorio_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE calorio_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE calorio TO calorio_user;
\q
EOF
```

## Шаг 3: Деплой проекта

```bash
# Переключиться на пользователя calorio
sudo su - calorio
cd /var/www/calorio

# Клонировать проект (замените URL на ваш репозиторий)
git clone https://github.com/yourusername/calorio.git .

# Создать виртуальное окружение
python3.11 -m venv venv
source venv/bin/activate

# Установить зависимости
pip install --upgrade pip
pip install -r requirements.txt

# Настроить .env
cp .env.production .env
# Файл .env.production уже содержит правильные настройки

# Применить миграции
python manage.py migrate

# Создать суперпользователя
python manage.py createsuperuser

# Собрать статические файлы
python manage.py collectstatic --noinput

# Выйти из пользователя calorio
exit
```

## Шаг 4: Настройка systemd и Nginx

```bash
# Установить systemd service
sudo cp /var/www/calorio/scripts/calorio.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable calorio
sudo systemctl start calorio

# Установить Nginx конфигурацию
sudo cp /var/www/calorio/scripts/nginx_calorio.conf /etc/nginx/sites-available/calorio
sudo ln -s /etc/nginx/sites-available/calorio /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

## Шаг 5: Получить SSL сертификат

```bash
sudo certbot --nginx -d colories.ru -d www.colories.ru
```

## Шаг 6: Проверка

```bash
# Проверить health endpoint
curl http://colories.ru/api/health/

# Проверить HTTPS
curl https://colories.ru/api/health/

# Проверить документацию
curl https://colories.ru/api/docs/
```

## Готово! 🎉

API доступен по адресам:
- https://colories.ru/api/
- https://www.colories.ru/api/ (редирект на основной домен)

Документация:
- https://colories.ru/api/docs/
- https://colories.ru/api/redoc/

## Полезные команды

```bash
# Просмотр логов
sudo journalctl -u calorio -f
sudo tail -f /var/www/calorio/logs/gunicorn-error.log

# Перезапуск сервисов
sudo systemctl restart calorio
sudo systemctl restart nginx

# Обновление кода
sudo su - calorio
cd /var/www/calorio
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
exit
sudo systemctl restart calorio
```

## Автоматический деплой

```bash
sudo /var/www/calorio/scripts/deploy.sh
```

Подробная документация: [PRODUCTION_DEPLOY.md](PRODUCTION_DEPLOY.md)


