#!/bin/bash
# Финальный скрипт деплоя на сервер

SERVER="root@217.26.29.106"
PASSWORD="C&6!wMqm!wOZ"

echo "=========================================="
echo "Финальная настройка Calorio API"
echo "=========================================="
echo ""

# Создаём скрипт для выполнения на сервере
cat > /tmp/server_commands.sh << 'SERVERSCRIPT'
#!/bin/bash
set -e

echo "1. Настройка PostgreSQL..."
sudo -u postgres psql -c "SELECT 1 FROM pg_database WHERE datname='calorio'" | grep -q 1 || \
sudo -u postgres psql << 'EOF'
CREATE DATABASE calorio;
CREATE USER calorio_user WITH PASSWORD 'calorio_secure_2024';
ALTER ROLE calorio_user SET client_encoding TO 'utf8';
ALTER ROLE calorio_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE calorio_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE calorio TO calorio_user;
\q
EOF

echo "2. Создание пользователя calorio..."
id -u calorio &>/dev/null || useradd -m -s /bin/bash calorio
mkdir -p /var/www/calorio
chown calorio:calorio /var/www/calorio

echo "3. Клонирование проекта..."
sudo -u calorio bash << 'USERSCRIPT'
cd /var/www/calorio
if [ -d .git ]; then
    git pull origin main
else
    git clone https://github.com/moschin777-bot/calorio.git .
fi

echo "4. Создание виртуального окружения..."
python3.11 -m venv venv
source venv/bin/activate

echo "5. Установка зависимостей..."
pip install --upgrade pip
pip install -r requirements.txt

echo "6. Создание .env файла..."
cat > .env << 'ENVFILE'
SECRET_KEY=django-prod-$(openssl rand -hex 32)
DEBUG=False
ALLOWED_HOSTS=217.26.29.106,colories.ru,www.colories.ru
DATABASE_URL=postgresql://calorio_user:calorio_secure_2024@localhost:5432/calorio
OPENROUTER_API_KEY=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
PAYMENT_WEBHOOK_SECRET=webhook-$(openssl rand -hex 16)
CORS_ALLOWED_ORIGINS=https://colories.ru,https://www.colories.ru,http://colories.ru,http://www.colories.ru
ENVFILE

echo "7. Применение миграций..."
python manage.py migrate --noinput

echo "8. Сбор статических файлов..."
python manage.py collectstatic --noinput

echo "9. Создание директории для логов..."
mkdir -p logs

echo "Пользовательская часть завершена!"
USERSCRIPT

echo "10. Настройка systemd service..."
cat > /etc/systemd/system/calorio.service << 'SERVICEEOF'
[Unit]
Description=Calorio API Gunicorn daemon
After=network.target

[Service]
Type=notify
User=calorio
Group=calorio
WorkingDirectory=/var/www/calorio
Environment="PATH=/var/www/calorio/venv/bin"
ExecStart=/var/www/calorio/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/var/www/calorio/gunicorn.sock \
    --timeout 120 \
    --access-logfile /var/www/calorio/logs/gunicorn-access.log \
    --error-logfile /var/www/calorio/logs/gunicorn-error.log \
    --log-level info \
    calorio_api.wsgi:application

[Install]
WantedBy=multi-user.target
SERVICEEOF

systemctl daemon-reload
systemctl enable calorio
systemctl restart calorio

echo "11. Настройка Nginx..."
cat > /etc/nginx/sites-available/calorio << 'NGINXEOF'
upstream calorio_app {
    server unix:/var/www/calorio/gunicorn.sock fail_timeout=0;
}

server {
    listen 80;
    server_name 217.26.29.106 colories.ru www.colories.ru;
    client_max_body_size 10M;

    location /static/ {
        alias /var/www/calorio/staticfiles/;
    }

    location /media/ {
        alias /var/www/calorio/media/;
    }

    location / {
        proxy_pass http://calorio_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
NGINXEOF

ln -sf /etc/nginx/sites-available/calorio /etc/nginx/sites-enabled/calorio
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

echo ""
echo "=========================================="
echo "12. Проверка статуса сервисов..."
echo "=========================================="
systemctl status calorio --no-pager | head -n 15
echo ""
systemctl status nginx --no-pager | head -n 15

echo ""
echo "=========================================="
echo "13. Проверка API..."
echo "=========================================="
sleep 3
curl -s http://localhost/api/health/ || echo "API пока не отвечает, подождите несколько секунд..."

echo ""
echo "=========================================="
echo "✅ ДЕПЛОЙ ЗАВЕРШЁН!"
echo "=========================================="
echo ""
echo "API доступен по адресам:"
echo "  - http://217.26.29.106/api/"
echo "  - http://colories.ru/api/"
echo ""
echo "Документация:"
echo "  - http://colories.ru/api/docs/"
echo "  - http://colories.ru/api/redoc/"
echo ""
echo "Для получения SSL сертификата выполните:"
echo "  certbot --nginx -d colories.ru -d www.colories.ru"
echo ""
SERVERSCRIPT

chmod +x /tmp/server_commands.sh

echo "Подключение к серверу и выполнение деплоя..."
echo "Сервер: $SERVER"
echo ""

# Используем expect для автоматизации
expect << 'EXPECTEOF'
set timeout 600
set server "root@217.26.29.106"
set password "C&6!wMqm!wOZ"

spawn scp /tmp/server_commands.sh $server:/tmp/
expect "password:"
send "$password\r"
expect eof

spawn ssh $server
expect "password:"
send "$password\r"

expect "#"
send "chmod +x /tmp/server_commands.sh\r"
expect "#"
send "/tmp/server_commands.sh\r"

expect {
    "ДЕПЛОЙ ЗАВЕРШЁН!" {
        send "exit\r"
    }
    timeout {
        puts "\nTimeout - проверьте статус вручную"
        send "exit\r"
    }
}

expect eof
EXPECTEOF

echo ""
echo "=========================================="
echo "Проверка доступности API..."
echo "=========================================="
sleep 5
curl -s http://217.26.29.106/api/health/ && echo "" || echo "API пока недоступен, подождите..."

echo ""
echo "Готово! Проверьте работу API:"
echo "  curl http://217.26.29.106/api/health/"
echo "  curl http://colories.ru/api/health/"

