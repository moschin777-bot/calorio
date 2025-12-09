#!/bin/bash
# Скрипт деплоя Calorio API на production сервер
# Использование: ./deploy.sh

set -e  # Остановка при ошибке

echo "=========================================="
echo "Деплой Calorio API"
echo "=========================================="

# Переменные
PROJECT_DIR="/var/www/calorio"
VENV_DIR="$PROJECT_DIR/venv"
USER="calorio"

# Проверка, что скрипт запущен от имени root или с sudo
if [ "$EUID" -ne 0 ]; then 
    echo "Пожалуйста, запустите скрипт с sudo"
    exit 1
fi

# 1. Клонирование или обновление репозитория
echo "1. Обновление кода..."
if [ -d "$PROJECT_DIR/.git" ]; then
    cd $PROJECT_DIR
    sudo -u $USER git pull origin main
else
    echo "Клонирование репозитория..."
    sudo -u $USER git clone https://github.com/yourusername/calorio.git $PROJECT_DIR
    cd $PROJECT_DIR
fi

# 2. Создание виртуального окружения
echo "2. Настройка виртуального окружения..."
if [ ! -d "$VENV_DIR" ]; then
    sudo -u $USER python3.11 -m venv $VENV_DIR
fi

# 3. Установка зависимостей
echo "3. Установка зависимостей..."
sudo -u $USER $VENV_DIR/bin/pip install --upgrade pip
sudo -u $USER $VENV_DIR/bin/pip install -r requirements.txt

# 4. Проверка .env файла
echo "4. Проверка .env файла..."
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "ОШИБКА: Файл .env не найден!"
    echo "Скопируйте .env.production как .env и настройте переменные"
    exit 1
fi

# 5. Применение миграций
echo "5. Применение миграций..."
sudo -u $USER $VENV_DIR/bin/python manage.py migrate --noinput

# 6. Сбор статических файлов
echo "6. Сбор статических файлов..."
sudo -u $USER $VENV_DIR/bin/python manage.py collectstatic --noinput

# 7. Установка systemd service
echo "7. Установка systemd service..."
cp $PROJECT_DIR/scripts/calorio.service /etc/systemd/system/calorio.service
systemctl daemon-reload
systemctl enable calorio
systemctl restart calorio

# 8. Установка Nginx конфигурации
echo "8. Настройка Nginx..."
if [ ! -f /etc/nginx/sites-available/calorio ]; then
    cp $PROJECT_DIR/scripts/nginx_calorio.conf /etc/nginx/sites-available/calorio
    ln -sf /etc/nginx/sites-available/calorio /etc/nginx/sites-enabled/calorio
    # Удаление дефолтной конфигурации
    rm -f /etc/nginx/sites-enabled/default
fi

# Проверка конфигурации Nginx
nginx -t

# Перезапуск Nginx
systemctl restart nginx

# 9. Проверка статуса сервисов
echo "9. Проверка статуса сервисов..."
echo ""
echo "Статус Gunicorn:"
systemctl status calorio --no-pager | head -n 10
echo ""
echo "Статус Nginx:"
systemctl status nginx --no-pager | head -n 10

# 10. Проверка логов
echo ""
echo "10. Последние логи Gunicorn:"
tail -n 20 $PROJECT_DIR/logs/gunicorn-error.log

echo ""
echo "=========================================="
echo "Деплой завершён!"
echo "=========================================="
echo ""
echo "Проверьте работу API:"
echo "  curl http://217.26.29.106/api/health/"
echo "  curl http://colories.ru/api/health/"
echo ""
echo "Для получения SSL сертификата выполните:"
echo "  sudo certbot --nginx -d colories.ru -d www.colories.ru"
echo ""
echo "Просмотр логов:"
echo "  sudo journalctl -u calorio -f"
echo "  sudo tail -f /var/www/calorio/logs/gunicorn-error.log"


