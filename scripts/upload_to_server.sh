#!/bin/bash
# Скрипт для загрузки проекта на production сервер
# Использование: ./upload_to_server.sh

set -e

SERVER="root@217.26.29.106"
PROJECT_DIR="/var/www/calorio"

echo "=========================================="
echo "Загрузка проекта на сервер"
echo "=========================================="

# Проверка, что мы в корне проекта
if [ ! -f "manage.py" ]; then
    echo "ОШИБКА: Запустите скрипт из корня проекта"
    exit 1
fi

# 1. Создание архива проекта (исключая ненужные файлы)
echo "1. Создание архива..."
tar -czf /tmp/calorio.tar.gz \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='db.sqlite3' \
    --exclude='venv' \
    --exclude='media' \
    --exclude='staticfiles' \
    --exclude='logs' \
    --exclude='.pytest_cache' \
    --exclude='.coverage' \
    --exclude='htmlcov' \
    .

# 2. Загрузка архива на сервер
echo "2. Загрузка на сервер..."
scp /tmp/calorio.tar.gz $SERVER:/tmp/

# 3. Распаковка на сервере
echo "3. Распаковка на сервере..."
ssh $SERVER << 'EOF'
    # Создание директории если не существует
    sudo mkdir -p /var/www/calorio
    
    # Распаковка
    cd /var/www/calorio
    sudo tar -xzf /tmp/calorio.tar.gz
    
    # Установка владельца
    sudo chown -R calorio:calorio /var/www/calorio
    
    # Удаление архива
    rm /tmp/calorio.tar.gz
    
    echo "Проект загружен в /var/www/calorio"
EOF

# 4. Удаление локального архива
rm /tmp/calorio.tar.gz

echo ""
echo "=========================================="
echo "Загрузка завершена!"
echo "=========================================="
echo ""
echo "Следующие шаги на сервере:"
echo "  ssh $SERVER"
echo "  sudo su - calorio"
echo "  cd /var/www/calorio"
echo "  python3.11 -m venv venv"
echo "  source venv/bin/activate"
echo "  pip install -r requirements.txt"
echo "  cp .env.production .env"
echo "  python manage.py migrate"
echo "  python manage.py collectstatic --noinput"
echo "  exit"
echo "  sudo /var/www/calorio/scripts/deploy.sh"


