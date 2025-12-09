#!/usr/bin/expect -f
# Финальное исправление

set timeout 300
set server "root@217.26.29.106"
set password "C&6!wMqm!wOZ"

spawn ssh $server
expect "password:"
send "$password\r"

expect "#"

# Генерация SECRET_KEY
send "SECRET_KEY=\$(openssl rand -hex 32)\r"
expect "#"

# Создание .env
send "sudo -u calorio bash\r"
expect "$"
send "cd /var/www/calorio\r"
expect "$"
send "cat > .env << 'EOF'\nSECRET_KEY=django-prod-secure-key-abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890\nDEBUG=False\nALLOWED_HOSTS=217.26.29.106,colories.ru,www.colories.ru,localhost,127.0.0.1\nDATABASE_URL=postgresql://calorio_user:calorio_secure_2024@localhost:5432/calorio\nOPENROUTER_API_KEY=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\nPAYMENT_WEBHOOK_SECRET=webhook-secure-1234567890abcdef1234567890abcdef\nCORS_ALLOWED_ORIGINS=https://colories.ru,https://www.colories.ru,http://colories.ru,http://www.colories.ru,http://217.26.29.106\nEOF\r"
expect "$"
send "exit\r"

expect "#"
send "systemctl restart calorio\r"
expect "#"
send "sleep 3\r"
expect "#"

# Тестирование
send "curl -s http://localhost/api/health/\r"
expect "#"

send "exit\r"
expect eof

