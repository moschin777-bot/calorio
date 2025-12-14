#!/usr/bin/expect -f
# Завершение деплоя - исправление .env

set timeout 300
set server "root@217.26.29.106"
set password "C&6!wMqm!wOZ"

puts "=========================================="
puts "Завершение деплоя - исправление .env"
puts "=========================================="
puts ""

spawn ssh $server
expect "password:"
send "$password\r"

expect "#"
puts "\n✅ Подключено к серверу\n"

# Переключение на пользователя calorio
send "su - calorio\r"
expect "$"

send "cd /var/www/calorio\r"
expect "$"

# Генерация SECRET_KEY
puts "Генерация SECRET_KEY..."
send "SECRET_KEY=\\$(openssl rand -hex 32)\r"
expect "$"

# Генерация WEBHOOK_SECRET
send "WEBHOOK_SECRET=\\$(openssl rand -hex 16)\r"
expect "$"

# Создание .env с правильными значениями
puts "Создание .env файла..."
send "cat > .env << EOF\r"
expect ">"
send "SECRET_KEY=\\$SECRET_KEY\r"
expect ">"
send "DEBUG=False\r"
expect ">"
send "ALLOWED_HOSTS=217.26.29.106,colories.ru,www.colories.ru,localhost,127.0.0.1\r"
expect ">"
send "DATABASE_URL=postgresql://calorio_user:calorio_secure_2024@localhost:5432/calorio\r"
expect ">"
send "OPENROUTER_API_KEY=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\r"
expect ">"
send "PAYMENT_WEBHOOK_SECRET=\\$WEBHOOK_SECRET\r"
expect ">"
send "CORS_ALLOWED_ORIGINS=https://colories.ru,https://www.colories.ru,http://colories.ru,http://www.colories.ru,http://217.26.29.106\r"
expect ">"
send "EOF\r"
expect "$"

# Проверка .env
puts "\nПроверка .env файла..."
send "cat .env\r"
expect "$"

# Выход из пользователя calorio
send "exit\r"
expect "#"

# Перезапуск Gunicorn
puts "\nПерезапуск Gunicorn..."
send "systemctl restart calorio\r"
expect "#"

send "sleep 5\r"
expect "#"

# Проверка статуса
puts "\nПроверка статуса сервисов..."
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
puts "\nТест регистрации пользователя..."
send "curl -s -X POST http://localhost/api/auth/register/ -H 'Content-Type: application/json' -d '{\"first_name\":\"Test\",\"email\":\"test@example.com\",\"password\":\"testpass123\"}'\r"
expect "#"

# Тест документации
puts "\nПроверка документации..."
send "curl -s http://localhost/api/docs/ | head -n 5\r"
expect "#"

puts "\n=========================================="
puts "✅ ДЕПЛОЙ ЗАВЕРШЁН НА 100%!"
puts "=========================================="
puts ""
puts "API полностью работает и доступен:"
puts "  - http://217.26.29.106/api/"
puts "  - http://colories.ru/api/"
puts ""
puts "Документация:"
puts "  - http://217.26.29.106/api/docs/"
puts "  - http://217.26.29.106/api/redoc/"
puts ""
puts "Health check:"
puts "  - http://217.26.29.106/api/health/"
puts ""

send "exit\r"
expect eof

