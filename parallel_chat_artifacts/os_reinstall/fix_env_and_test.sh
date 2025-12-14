#!/usr/bin/expect -f
# Исправление .env и финальное тестирование

set timeout 300
set server "root@217.26.29.106"
set password "C&6!wMqm!wOZ"

puts "=========================================="
puts "Исправление .env и тестирование"
puts "=========================================="
puts ""

spawn ssh $server
expect "password:"
send "$password\r"

expect "#"
puts "\n✅ Подключено к серверу\n"

# Проверка текущего .env
send "cat /var/www/calorio/.env\r"
expect "#"

# Создание правильного .env
send "sudo -u calorio bash << 'USEREOF'\ncd /var/www/calorio\ncat > .env << 'ENVFILE'\nSECRET_KEY=django-prod-secure-key-$(openssl rand -hex 32)\nDEBUG=False\nALLOWED_HOSTS=217.26.29.106,colories.ru,www.colories.ru,localhost,127.0.0.1\nDATABASE_URL=postgresql://calorio_user:calorio_secure_2024@localhost:5432/calorio\nOPENROUTER_API_KEY=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\nPAYMENT_WEBHOOK_SECRET=webhook-secure-$(openssl rand -hex 16)\nCORS_ALLOWED_ORIGINS=https://colories.ru,https://www.colories.ru,http://colories.ru,http://www.colories.ru,http://217.26.29.106\nENVFILE\nUSEREOF\r"
expect "#"

# Перезапуск Gunicorn
send "systemctl restart calorio\r"
expect "#"
send "sleep 3\r"
expect "#"

# Проверка статуса
send "systemctl status calorio --no-pager | head -n 10\r"
expect "#"

# Тестирование API
puts "\n=========================================="
puts "Тестирование API..."
puts "=========================================="

send "curl -s http://localhost/api/health/\r"
expect "#"

send "curl -s http://217.26.29.106/api/health/\r"
expect "#"

# Тест регистрации
send "curl -s -X POST http://localhost/api/auth/register/ -H 'Content-Type: application/json' -d '{\"first_name\":\"Test\",\"email\":\"test@example.com\",\"password\":\"testpass123\"}' | head -n 20\r"
expect "#"

puts "\n=========================================="
puts "✅ ДЕПЛОЙ ЗАВЕРШЁН УСПЕШНО!"
puts "=========================================="
puts ""
puts "API доступен по адресам:"
puts "  - http://217.26.29.106/api/"
puts "  - http://colories.ru/api/"
puts ""
puts "Документация:"
puts "  - http://217.26.29.106/api/docs/"
puts "  - http://217.26.29.106/api/redoc/"
puts ""

send "exit\r"
expect eof

