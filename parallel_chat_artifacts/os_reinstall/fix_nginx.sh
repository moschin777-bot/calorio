#!/usr/bin/expect -f
# Исправление конфигурации Nginx

set timeout 300
set server "root@217.26.29.106"
set password "C&6!wMqm!wOZ"

puts "=========================================="
puts "Исправление Nginx"
puts "=========================================="
puts ""

spawn ssh $server
expect "password:"
send "$password\r"

expect "#"
puts "\n✅ Подключено к серверу\n"

# Проверка текущей конфигурации
send "cat /etc/nginx/sites-available/calorio\r"
expect "#"

# Создание правильной конфигурации
send "cat > /etc/nginx/sites-available/calorio << 'NGINXEOF'\nupstream calorio_app {\n    server unix:/var/www/calorio/gunicorn.sock fail_timeout=0;\n}\n\nserver {\n    listen 80;\n    server_name 217.26.29.106 colories.ru www.colories.ru;\n    client_max_body_size 10M;\n\n    location /static/ {\n        alias /var/www/calorio/staticfiles/;\n    }\n\n    location /media/ {\n        alias /var/www/calorio/media/;\n    }\n\n    location / {\n        proxy_pass http://calorio_app;\n        proxy_set_header Host \\\$host;\n        proxy_set_header X-Real-IP \\\$remote_addr;\n        proxy_set_header X-Forwarded-For \\\$proxy_add_x_forwarded_for;\n        proxy_set_header X-Forwarded-Proto \\\$scheme;\n        proxy_redirect off;\n    }\n}\nNGINXEOF\r"
expect "#"

# Активация конфигурации
send "ln -sf /etc/nginx/sites-available/calorio /etc/nginx/sites-enabled/calorio\r"
expect "#"
send "rm -f /etc/nginx/sites-enabled/default\r"
expect "#"

# Проверка конфигурации
send "nginx -t\r"
expect "#"

# Перезапуск Nginx
send "systemctl restart nginx\r"
expect "#"

# Проверка статуса
send "systemctl status nginx --no-pager | head -n 10\r"
expect "#"

# Проверка API
send "sleep 2\r"
expect "#"
send "curl -s http://localhost/api/health/\r"
expect "#"

puts "\n=========================================="
puts "✅ Nginx настроен!"
puts "=========================================="

send "exit\r"
expect eof

