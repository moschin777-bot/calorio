#!/usr/bin/expect -f
# Исправление и повторный деплой

set timeout 600
set server "root@217.26.29.106"
set password "C&6!wMqm!wOZ"

puts "=========================================="
puts "Исправление и повторный деплой"
puts "=========================================="
puts ""

spawn ssh $server
expect "password:"
send "$password\r"

expect "#"
puts "\n✅ Подключено к серверу\n"

# Обновление кода
send "cd /var/www/calorio\r"
expect "#"
send "sudo -u calorio git pull origin main\r"
expect "#"

# Установка зависимостей
send "sudo -u calorio bash << 'EOF'\ncd /var/www/calorio\nsource venv/bin/activate\npip install -r requirements.txt\npython manage.py migrate --noinput\npython manage.py collectstatic --noinput\nEOF\r"
expect "#"

# Перезапуск сервиса
send "systemctl restart calorio\r"
expect "#"
send "sleep 5\r"
expect "#"

# Проверка статуса
send "systemctl status calorio --no-pager | head -n 15\r"
expect "#"

# Проверка API
send "curl -s http://localhost/api/health/\r"
expect "#"

puts "\n=========================================="
puts "✅ Деплой завершён!"
puts "=========================================="

send "exit\r"
expect eof

