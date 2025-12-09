# Чеклист деплоя Calorio API на Production

## Информация о сервере
- **IP**: 217.26.29.106
- **Домены**: colories.ru, www.colories.ru
- **Пароль**: C&6!wMqm!wOZ

---

## ✅ Чеклист действий

### 1. Подготовка локально

- [x] DEBUG=False в settings.py по умолчанию
- [x] Создан .env.production с правильными настройками
- [x] Все скрипты деплоя созданы и протестированы
- [x] requirements.txt актуален
- [ ] Все изменения закоммичены в git
- [ ] Создан тег версии (опционально)

### 2. Подключение к серверу

```bash
ssh root@217.26.29.106
# Пароль: C&6!wMqm!wOZ
```

### 3. Установка ПО на сервере

Выполните на сервере:

```bash
# Скачайте и запустите скрипт установки
wget https://raw.githubusercontent.com/yourusername/calorio/main/scripts/server_setup.sh
chmod +x server_setup.sh
sudo ./server_setup.sh
```

Или вручную выполните команды из `scripts/server_setup.sh`

**Что будет установлено:**
- [ ] Python 3.11
- [ ] PostgreSQL
- [ ] Nginx
- [ ] Certbot
- [ ] Создан пользователь `calorio`
- [ ] Создана база данных `calorio`
- [ ] Созданы необходимые директории

### 4. Загрузка проекта на сервер

**Вариант A: Через Git (рекомендуется)**

```bash
sudo su - calorio
cd /var/www/calorio
git clone https://github.com/yourusername/calorio.git .
```

**Вариант B: Через SCP (если нет git репозитория)**

Локально:
```bash
./scripts/upload_to_server.sh
```

### 5. Настройка проекта на сервере

```bash
sudo su - calorio
cd /var/www/calorio

# Создать виртуальное окружение
python3.11 -m venv venv
source venv/bin/activate

# Установить зависимости
pip install --upgrade pip
pip install -r requirements.txt

# Настроить .env
cp .env.production .env

# Применить миграции
python manage.py migrate

# Создать суперпользователя
python manage.py createsuperuser
# Email: admin@colories.ru
# Password: (придумайте надёжный пароль)

# Собрать статические файлы
python manage.py collectstatic --noinput

# Выйти из пользователя calorio
exit
```

**Проверка:**
- [ ] Виртуальное окружение создано
- [ ] Зависимости установлены
- [ ] .env файл настроен
- [ ] Миграции применены
- [ ] Суперпользователь создан
- [ ] Статические файлы собраны

### 6. Настройка systemd service

```bash
# Скопировать service файл
sudo cp /var/www/calorio/scripts/calorio.service /etc/systemd/system/

# Перезагрузить systemd
sudo systemctl daemon-reload

# Включить автозапуск
sudo systemctl enable calorio

# Запустить сервис
sudo systemctl start calorio

# Проверить статус
sudo systemctl status calorio
```

**Проверка:**
- [ ] Service файл установлен
- [ ] Gunicorn запущен без ошибок
- [ ] Socket файл создан: `/var/www/calorio/calorio.sock`

### 7. Настройка Nginx

```bash
# Скопировать конфигурацию
sudo cp /var/www/calorio/scripts/nginx_calorio.conf /etc/nginx/sites-available/calorio

# Создать символическую ссылку
sudo ln -s /etc/nginx/sites-available/calorio /etc/nginx/sites-enabled/

# Удалить дефолтную конфигурацию
sudo rm -f /etc/nginx/sites-enabled/default

# Проверить конфигурацию
sudo nginx -t

# Перезапустить Nginx
sudo systemctl restart nginx
```

**Проверка:**
- [ ] Nginx конфигурация установлена
- [ ] Конфигурация валидна (nginx -t)
- [ ] Nginx перезапущен без ошибок

### 8. Проверка DNS

Убедитесь, что DNS записи настроены:

```bash
# Проверка DNS
nslookup colories.ru
nslookup www.colories.ru
```

**Должно быть:**
- [ ] A запись: colories.ru → 217.26.29.106
- [ ] A запись: www.colories.ru → 217.26.29.106

### 9. Проверка работы (HTTP)

```bash
# На сервере
curl http://localhost/api/health/
curl http://217.26.29.106/api/health/

# Локально
curl http://217.26.29.106/api/health/
curl http://colories.ru/api/health/
```

**Ожидаемый ответ:**
```json
{"status":"ok","timestamp":"..."}
```

**Проверка:**
- [ ] Health endpoint отвечает
- [ ] API доступен по IP
- [ ] API доступен по домену

### 10. Получение SSL сертификата

```bash
# Получить сертификат от Let's Encrypt
sudo certbot --nginx -d colories.ru -d www.colories.ru

# Certbot автоматически:
# - Получит сертификат
# - Настроит HTTPS в Nginx
# - Настроит редирект с HTTP на HTTPS
```

**Проверка:**
- [ ] SSL сертификат получен
- [ ] HTTPS работает
- [ ] Редирект с HTTP на HTTPS работает
- [ ] Редирект с www на основной домен работает

### 11. Финальная проверка

```bash
# Проверка HTTPS
curl https://colories.ru/api/health/

# Проверка документации
curl https://colories.ru/api/docs/

# Проверка регистрации
curl -X POST https://colories.ru/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123","first_name":"Test"}'
```

**Проверка всех эндпоинтов:**
- [ ] GET /api/health/ - работает
- [ ] GET /api/docs/ - документация доступна
- [ ] GET /api/redoc/ - документация доступна
- [ ] POST /api/auth/register/ - регистрация работает
- [ ] POST /api/auth/login/ - авторизация работает
- [ ] Статические файлы загружаются
- [ ] Admin панель доступна: https://colories.ru/admin/

### 12. Настройка мониторинга

```bash
# Просмотр логов
sudo journalctl -u calorio -f
sudo tail -f /var/www/calorio/logs/gunicorn-error.log
sudo tail -f /var/log/nginx/calorio-error.log
```

**Настройка автоматических бэкапов:**

```bash
# Создать директорию для бэкапов
sudo mkdir -p /backups

# Добавить в crontab
sudo crontab -e

# Добавить строку (бэкап каждый день в 2:00)
0 2 * * * sudo -u postgres pg_dump calorio > /backups/calorio_$(date +\%Y\%m\%d).sql
```

**Проверка:**
- [ ] Логи доступны и не содержат ошибок
- [ ] Настроен автоматический бэкап БД
- [ ] Настроен мониторинг (опционально)

### 13. Настройка Firewall (рекомендуется)

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

**Проверка:**
- [ ] Firewall настроен
- [ ] Порты 22, 80, 443 открыты
- [ ] Остальные порты закрыты

---

## 🎉 Деплой завершён!

### Адреса API:
- **Production**: https://colories.ru/api/
- **Документация**: https://colories.ru/api/docs/
- **ReDoc**: https://colories.ru/api/redoc/
- **Admin**: https://colories.ru/admin/

### Полезные команды:

**Просмотр логов:**
```bash
sudo journalctl -u calorio -f
sudo tail -f /var/www/calorio/logs/gunicorn-error.log
sudo tail -f /var/log/nginx/calorio-error.log
```

**Перезапуск сервисов:**
```bash
sudo systemctl restart calorio
sudo systemctl restart nginx
```

**Обновление кода:**
```bash
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

**Автоматический деплой:**
```bash
sudo /var/www/calorio/scripts/deploy.sh
```

---

## 📚 Дополнительная документация

- [QUICK_DEPLOY.md](QUICK_DEPLOY.md) - Быстрый старт
- [PRODUCTION_DEPLOY.md](PRODUCTION_DEPLOY.md) - Подробная инструкция
- [DEPLOYMENT.md](DEPLOYMENT.md) - Общее руководство по деплою

---

## 🆘 Troubleshooting

### Проблема: 502 Bad Gateway
```bash
sudo systemctl status calorio
sudo journalctl -u calorio -n 50
```

### Проблема: Permission denied
```bash
sudo chown -R calorio:calorio /var/www/calorio
```

### Проблема: Database connection failed
```bash
sudo systemctl status postgresql
cat /var/www/calorio/.env | grep DATABASE_URL
```

### Проблема: Static files not loading
```bash
sudo su - calorio
cd /var/www/calorio
source venv/bin/activate
python manage.py collectstatic --noinput --clear
exit
sudo chown -R calorio:calorio /var/www/calorio/staticfiles
```


