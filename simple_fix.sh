#!/bin/bash
scp .env.server root@217.26.29.106:/tmp/env_new
ssh root@217.26.29.106 << 'REMOTE'
cp /tmp/env_new /var/www/calorio/.env
chown calorio:calorio /var/www/calorio/.env
systemctl restart calorio
sleep 5
systemctl status calorio --no-pager | head -n 10
echo ""
echo "Тестирование API:"
curl -s http://localhost/api/health/
echo ""
curl -s -X POST http://localhost/api/auth/register/ -H 'Content-Type: application/json' -d '{"first_name":"Test","email":"test@example.com","password":"testpass123"}' | head -n 20
REMOTE
