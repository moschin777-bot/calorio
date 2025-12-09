#!/bin/bash
# Скрипт для установки необходимого ПО на Ubuntu сервере
# Для деплоя Calorio API

set -e  # Остановка при ошибке

echo "=========================================="
echo "Установка ПО для Calorio API"
echo "=========================================="

# Обновление системы
echo "1. Обновление системы..."
sudo apt update
sudo apt upgrade -y

# Установка Python 3.11 и зависимостей
echo "2. Установка Python 3.11..."
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Установка PostgreSQL
echo "3. Установка PostgreSQL..."
sudo apt install -y postgresql postgresql-contrib libpq-dev

# Установка Nginx
echo "4. Установка Nginx..."
sudo apt install -y nginx

# Установка дополнительных инструментов
echo "5. Установка дополнительных инструментов..."
sudo apt install -y git curl wget build-essential

# Установка Certbot для SSL
echo "6. Установка Certbot для SSL..."
sudo apt install -y certbot python3-certbot-nginx

# Создание пользователя для приложения (если не существует)
echo "7. Создание пользователя calorio..."
if ! id "calorio" &>/dev/null; then
    sudo useradd -m -s /bin/bash calorio
    echo "Пользователь calorio создан"
else
    echo "Пользователь calorio уже существует"
fi

# Создание директорий для проекта
echo "8. Создание директорий..."
sudo mkdir -p /var/www/calorio
sudo mkdir -p /var/www/calorio/logs
sudo mkdir -p /var/www/calorio/media
sudo mkdir -p /var/www/calorio/staticfiles
sudo chown -R calorio:calorio /var/www/calorio

# Настройка PostgreSQL
echo "9. Настройка PostgreSQL..."
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname = 'calorio'" | grep -q 1 || \
sudo -u postgres psql <<EOF
CREATE DATABASE calorio;
CREATE USER calorio_user WITH PASSWORD 'C&6!wMqm!wOZ';
ALTER ROLE calorio_user SET client_encoding TO 'utf8';
ALTER ROLE calorio_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE calorio_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE calorio TO calorio_user;
\q
EOF

echo "=========================================="
echo "Установка завершена!"
echo "=========================================="
echo ""
echo "Следующие шаги:"
echo "1. Клонируйте репозиторий в /var/www/calorio"
echo "2. Создайте виртуальное окружение"
echo "3. Установите зависимости из requirements.txt"
echo "4. Скопируйте .env.production как .env"
echo "5. Запустите миграции"
echo "6. Настройте systemd service"
echo "7. Настройте Nginx"
echo "8. Получите SSL сертификат"


