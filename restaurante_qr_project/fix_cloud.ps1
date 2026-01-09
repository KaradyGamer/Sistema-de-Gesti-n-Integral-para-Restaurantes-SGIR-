# ==============================
# FIX SGIR CLOUD (PowerShell)
# ==============================
# Reconstruye contenedores y verifica PostgreSQL

Write-Host "=============================="
Write-Host " FIX SGIR CLOUD (PostgreSQL)"
Write-Host "=============================="

Write-Host "`n=== [1] Detener contenedores existentes ==="
docker compose -f docker-compose.prod.yml down

Write-Host "`n=== [2] Reconstruir y recrear contenedores ==="
docker compose -f docker-compose.prod.yml up -d --build --force-recreate

Write-Host "`n=== [3] Esperar 30 segundos para que servicios estén listos ==="
Start-Sleep -Seconds 30

Write-Host "`n=== [4] Verificar estado de contenedores ==="
docker compose -f docker-compose.prod.yml ps

Write-Host "`n=== [5] Verificar VENDOR (debe ser postgresql) ==="
docker compose -f docker-compose.prod.yml exec web python manage.py shell -c "from django.db import connection; print('VENDOR=',connection.vendor)"

Write-Host "`n=== [6] Verificar ENGINE/HOST/NAME ==="
docker compose -f docker-compose.prod.yml exec web python manage.py shell -c "from django.conf import settings; print('ENGINE=',settings.DATABASES['default']['ENGINE']); print('HOST=',settings.DATABASES['default'].get('HOST')); print('NAME=',settings.DATABASES['default'].get('NAME'))"

Write-Host "`n=== [7] Verificar variables de entorno en contenedor ==="
docker compose -f docker-compose.prod.yml exec web sh -c "env | grep POSTGRES_ | sort"

Write-Host "`n=============================="
Write-Host " VERIFICACIÓN COMPLETADA"
Write-Host "=============================="
Write-Host "`nSiguientes pasos (si VENDOR=postgresql):"
Write-Host "1. docker compose -f docker-compose.prod.yml exec web python manage.py migrate"
Write-Host "2. docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser"
Write-Host "3. ./auditoria_completa.sh (o .\auditoria_completa.ps1)"
Write-Host ""