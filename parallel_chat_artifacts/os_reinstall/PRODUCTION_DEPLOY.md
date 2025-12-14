# Инструкция по деплою Calorio API на Production

## Информация о сервере

- **IP адрес**: 217.26.29.106
- **Домены**: colories.ru, www.colories.ru
- **Пароль**: C&6!wMqm!wOZ
- **ОС**: Ubuntu (предполагается)

## Быстрый старт

### 1. Подключение к серверу

```bash
ssh root@217.26.29.106
# Введите пароль: C&6!wMqm!wOZ
```

### 2. Установка необходимого ПО

```bash
# Скачайте скрипт установки
wget https://raw.githubusercontent.com/yourusername/calorio/main/scripts/server_setup.sh

# Или скопируйте вручную содержимое scripts/server_setup.sh

# Сделайте скрипт исполняемым
chmod +x server_setup.sh

# Запустите установку
sudo ./server_setup.sh
```

Скрипт установит:
- Python 3.11
- PostgreSQL
- Nginx
- Certbot (для SSL)
- Создаст пользователя `calorio`
- Создаст базу данных `calorio` с пользователем `calorio_user`

### 3. Клонирование проекта

```bash
# Переключитесь на пользователя calorio
sudo su - calorio

# Перейдите в директорию проекта
cd /var/www/calorio

# Клонируйте репозиторий
git clone https://github.com/yourusername/calorio.git .

# Или загрузите проект через scp/rsync
```

### 4. Настройка проекта

```bash
# Создайте виртуальное окружение
python3.11 -m venv venv

# Активируйте виртуальное окружение
source venv/bin/activate

# Установите зависимости
pip install --upgrade pip
pip install -r requirements.txt

# Скопируйте production конфигурацию
cp .env.production .env

# Отредактируйте .env при необходимости
nano .env
```

### 5. Инициализация базы данных

```bash
# Примените миграции
python manage.py migrate

# Создайте суперпользователя
python manage.py createsuperuser

# Соберите статические файлы
python manage.py collectstatic --noinput

# Выйдите из пользователя calorio
exit
```

### 6. Настройка systemd service

```bash
# Скопируйте service файл
sudo cp /var/www/calorio/scripts/calorio.service /etc/systemd/system/

# Перезагрузите systemd
sudo systemctl daemon-reload

# Включите автозапуск
sudo systemctl enable calorio

# Запустите сервис
sudo systemctl start calorio

# Проверьте статус
sudo systemctl status calorio
```

### 7. Настройка Nginx

```bash
# Скопируйте конфигурацию
sudo cp /var/www/calorio/scripts/nginx_calorio.conf /etc/nginx/sites-available/calorio

# Создайте символическую ссылку
sudo ln -s /etc/nginx/sites-available/calorio /etc/nginx/sites-enabled/

# Удалите дефолтную конфигурацию
sudo rm /etc/nginx/sites-enabled/default

# Проверьте конфигурацию
sudo nginx -t

# Перезапустите Nginx
sudo systemctl restart nginx
```

### 8. Настройка DNS

Убедитесь, что DNS записи настроены правильно:

```
A запись: colories.ru -> 217.26.29.106
A запись: www.colories.ru -> 217.26.29.106
```

### 9. Получение SSL сертификата

```bash
# Получите SSL сертификат от Let's Encrypt
sudo certbot --nginx -d colories.ru -d www.colories.ru

# Certbot автоматически настроит HTTPS редирект
```

### 10. Проверка работы

```bash
# Проверка health endpoint
curl http://colories.ru/api/health/

# Проверка HTTPS (после получения SSL)
curl https://colories.ru/api/health/

# Проверка документации
curl https://colories.ru/api/docs/
```

## Автоматический деплой

Для автоматизации деплоя используйте скрипт `deploy.sh`:

```bash
# Сделайте скрипт исполняемым
chmod +x /var/www/calorio/scripts/deploy.sh

# Запустите деплой
sudo /var/www/calorio/scripts/deploy.sh
```

## Обновление приложения

```bash
# Переключитесь на пользователя calorio
sudo su - calorio
cd /var/www/calorio

# Получите последние изменения
git pull origin main

# Активируйте виртуальное окружение
source venv/bin/activate

# Обновите зависимости
pip install -r requirements.txt

# Примените миграции
python manage.py migrate

# Соберите статические файлы
python manage.py collectstatic --noinput

# Выйдите из пользователя
exit

# Перезапустите сервис
sudo systemctl restart calorio
```

## Мониторинг и логи

### Просмотр логов Gunicorn

```bash
# Логи через systemd
sudo journalctl -u calorio -f

# Логи приложения
sudo tail -f /var/www/calorio/logs/gunicorn-error.log
sudo tail -f /var/www/calorio/logs/gunicorn-access.log
```

### Просмотр логов Nginx

```bash
sudo tail -f /var/log/nginx/calorio-access.log
sudo tail -f /var/log/nginx/calorio-error.log
```

### Просмотр логов Django

```bash
sudo tail -f /var/www/calorio/logs/django.log
```

### Статус сервисов

```bash
# Статус Gunicorn
sudo systemctl status calorio

# Статус Nginx
sudo systemctl status nginx

# Статус PostgreSQL
sudo systemctl status postgresql
```

## Управление сервисами

```bash
# Перезапуск Gunicorn
sudo systemctl restart calorio

# Остановка Gunicorn
sudo systemctl stop calorio

# Запуск Gunicorn
sudo systemctl start calorio

# Перезагрузка конфигурации (без остановки)
sudo systemctl reload calorio

# Перезапуск Nginx
sudo systemctl restart nginx
```

## Бэкапы

### Бэкап базы данных

```bash
# Создание бэкапа
sudo -u postgres pg_dump calorio > /backups/calorio_$(date +%Y%m%d_%H%M%S).sql

# Восстановление из бэкапа
sudo -u postgres psql calorio < /backups/calorio_20241209_120000.sql
```

### Автоматический бэкап (cron)

```bash
# Откройте crontab
sudo crontab -e

# Добавьте задачу (бэкап каждый день в 2:00)
0 2 * * * sudo -u postgres pg_dump calorio > /backups/calorio_$(date +\%Y\%m\%d).sql
```

## Troubleshooting

### Проблема: 502 Bad Gateway

```bash
# Проверьте статус Gunicorn
sudo systemctl status calorio

# Проверьте логи
sudo journalctl -u calorio -n 50

# Проверьте socket файл
ls -la /var/www/calorio/calorio.sock
```

### Проблема: Permission denied

```bash
# Проверьте владельца файлов
ls -la /var/www/calorio

# Исправьте права
sudo chown -R calorio:calorio /var/www/calorio
```

### Проблема: Database connection failed

```bash
# Проверьте статус PostgreSQL
sudo systemctl status postgresql

# Проверьте подключение
sudo -u postgres psql -c "SELECT 1"

# Проверьте .env файл
cat /var/www/calorio/.env | grep DATABASE_URL
```

### Проблема: Static files not loading

```bash
# Соберите статические файлы заново
sudo su - calorio
cd /var/www/calorio
source venv/bin/activate
python manage.py collectstatic --noinput --clear
exit

# Проверьте права
sudo chown -R calorio:calorio /var/www/calorio/staticfiles
```

## Безопасность

### Firewall (UFW)

```bash
# Установка UFW
sudo apt install ufw

# Разрешить SSH
sudo ufw allow 22/tcp

# Разрешить HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Включить firewall
sudo ufw enable

# Проверить статус
sudo ufw status
```

### Fail2Ban (защита от брутфорса)

```bash
# Установка
sudo apt install fail2ban

# Создание конфигурации для Nginx
sudo nano /etc/fail2ban/jail.local
```

Добавьте:
```ini
[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/calorio-error.log
```

```bash
# Перезапуск Fail2Ban
sudo systemctl restart fail2ban
```

## Производительность

### Оптимизация PostgreSQL

```bash
# Откройте конфигурацию
sudo nano /etc/postgresql/*/main/postgresql.conf

# Рекомендуемые настройки для небольшого сервера
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
min_wal_size = 1GB
max_wal_size = 4GB

# Перезапуск PostgreSQL
sudo systemctl restart postgresql
```

### Мониторинг ресурсов

```bash
# Использование CPU и памяти
htop

# Использование диска
df -h

# Активные процессы
ps aux | grep gunicorn
```

## Контакты

При возникновении проблем:
- Email: support@calorio.app
- GitHub Issues: https://github.com/yourusername/calorio/issues


