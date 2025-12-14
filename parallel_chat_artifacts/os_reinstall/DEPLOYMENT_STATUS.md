# Статус деплоя Calorio API

## ✅ Выполненные задачи

### 1. Проверка проекта
- ✅ Все файлы проекта проверены на ошибки
- ✅ System check: 0 проблем
- ✅ Линтер: 0 ошибок
- ✅ Миграции: все применены и актуальны

### 2. Тестирование
- ✅ Запущены все тесты: **177 тестов прошли успешно**
- ✅ Покрытие кода: **86%** (требуется минимум 80%)
- ✅ Тесты аутентификации: 39/39 ✅
- ✅ Тесты профиля: 27/27 ✅
- ✅ Тесты блюд: 52/52 ✅
- ✅ Тесты целей КБЖУ: 40/40 ✅
- ✅ Тесты управления днями: 18/18 ✅
- ✅ Тесты подписок: 10/10 ✅
- ✅ Тесты инфраструктуры: 30/30 ✅

### 3. Git
- ✅ Все изменения добавлены в git
- ✅ Коммит создан с описанием изменений
- ✅ Изменения загружены в GitHub (origin/main)

### 4. Подготовка к деплою
- ✅ Созданы скрипты деплоя
- ✅ Создана документация по деплою
- ✅ Настроены production конфигурации
- ✅ Подготовлены systemd service и Nginx конфигурации

## 📋 Готовность к деплою

Проект **полностью готов** к деплою на production сервер.

### Информация о сервере
- **IP**: 217.26.29.106
- **Домены**: colories.ru, www.colories.ru
- **Пользователь**: root
- **Пароль**: C&6!wMqm!wOZ

## 🚀 Инструкция по деплою

### Вариант 1: Автоматический деплой (рекомендуется)

```bash
# Подключитесь к серверу
ssh root@217.26.29.106
# Пароль: C&6!wMqm!wOZ

# Выполните команды деплоя
curl -sSL https://raw.githubusercontent.com/moschin777-bot/calorio/main/scripts/server_setup.sh | bash
```

### Вариант 2: Ручной деплой

Подробная инструкция находится в файле `PRODUCTION_DEPLOY.md`

Основные шаги:

1. **Установка ПО**
```bash
apt update && apt upgrade -y
apt install -y python3.11 python3.11-venv python3.11-dev git nginx postgresql postgresql-contrib
```

2. **Настройка PostgreSQL**
```bash
sudo -u postgres psql
CREATE DATABASE calorio;
CREATE USER calorio_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE calorio TO calorio_user;
\q
```

3. **Клонирование проекта**
```bash
useradd -m -s /bin/bash calorio
mkdir -p /var/www/calorio
chown calorio:calorio /var/www/calorio
sudo su - calorio
cd /var/www/calorio
git clone https://github.com/moschin777-bot/calorio.git .
```

4. **Настройка виртуального окружения**
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

5. **Настройка .env**
```bash
cp .env.production .env
nano .env  # Отредактируйте настройки
```

6. **Инициализация базы данных**
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
exit
```

7. **Настройка systemd**
```bash
cp /var/www/calorio/scripts/calorio.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable calorio
systemctl start calorio
```

8. **Настройка Nginx**
```bash
cp /var/www/calorio/scripts/nginx_calorio.conf /etc/nginx/sites-available/calorio
ln -sf /etc/nginx/sites-available/calorio /etc/nginx/sites-enabled/calorio
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx
```

9. **Получение SSL сертификата**
```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d colories.ru -d www.colories.ru
```

## ✅ Проверка работоспособности

После деплоя проверьте:

```bash
# Health check
curl http://217.26.29.106/api/health/
curl http://colories.ru/api/health/

# API документация
curl http://colories.ru/api/docs/

# Регистрация пользователя
curl -X POST http://colories.ru/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"first_name":"Test","email":"test@example.com","password":"testpass123"}'
```

## 📊 Статистика проекта

- **Всего файлов**: ~50
- **Строк кода**: ~2400
- **Тестов**: 177
- **Покрытие**: 86%
- **Эндпоинтов API**: 25+
- **Моделей**: 9
- **Сериализаторов**: 15+

## 🔧 Полезные команды

### Просмотр логов
```bash
# Логи Gunicorn
journalctl -u calorio -f
tail -f /var/www/calorio/logs/gunicorn-error.log

# Логи Nginx
tail -f /var/log/nginx/error.log

# Логи Django
tail -f /var/www/calorio/logs/django.log
```

### Перезапуск сервисов
```bash
systemctl restart calorio
systemctl restart nginx
```

### Обновление проекта
```bash
sudo su - calorio
cd /var/www/calorio
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
exit
systemctl restart calorio
```

## 📝 Следующие шаги

1. ✅ Проект готов к деплою
2. ⏳ Подключение к серверу и выполнение деплоя
3. ⏳ Проверка работоспособности API
4. ⏳ Настройка SSL сертификата
5. ⏳ Настройка мониторинга и бэкапов

## 🎯 Готово к использованию

После деплоя фронтенд сможет подключиться к API по адресу:
- **HTTP**: http://colories.ru/api/
- **HTTPS**: https://colories.ru/api/ (после настройки SSL)

Документация API доступна по адресу:
- **Swagger UI**: https://colories.ru/api/docs/
- **ReDoc**: https://colories.ru/api/redoc/

