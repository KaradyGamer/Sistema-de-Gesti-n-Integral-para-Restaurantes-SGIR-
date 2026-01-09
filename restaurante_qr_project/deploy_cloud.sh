#!/bin/bash
# ============================================
# DESPLIEGUE COMPLETO EN CLOUD - SGIR
# Postgres + Healthcheck Fix
# ============================================

set -e  # Detener si hay error

echo "=========================================="
echo "SGIR - Despliegue en Cloud (PostgreSQL)"
echo "=========================================="

# D) REBUILD + RESET DEL WEB
echo ""
echo "=== PASO 1: Deteniendo contenedores existentes ==="
docker compose -f docker-compose.prod.yml down

echo ""
echo "=== PASO 2: Reconstruyendo y levantando servicios ==="
docker compose -f docker-compose.prod.yml up -d --build

echo ""
echo "=== PASO 3: Esperando que los servicios estén listos (30s) ==="
sleep 30

# E) CONFIRMAR QUE YA ES POSTGRES
echo ""
echo "=== PASO 4: Verificando motor de base de datos ==="
docker compose -f docker-compose.prod.yml exec web python manage.py shell -c "from django.conf import settings; print('ENGINE=',settings.DATABASES['default']['ENGINE'],'HOST=',settings.DATABASES['default'].get('HOST'),'NAME=',settings.DATABASES['default'].get('NAME'))"

# F) MIGRACIONES
echo ""
echo "=== PASO 5: Aplicando migraciones ==="
docker compose -f docker-compose.prod.yml exec web python manage.py migrate

echo ""
echo "=== PASO 6: Creando superusuario ==="
echo "IMPORTANTE: Completa los datos del superusuario a continuación"
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# G) VERIFICAR HEALTHY + SUPERUSERS
echo ""
echo "=== PASO 7: Verificando estado de contenedores ==="
docker compose -f docker-compose.prod.yml ps

echo ""
echo "=== PASO 8: Verificando superusuarios ==="
docker compose -f docker-compose.prod.yml exec web python manage.py shell -c "from django.contrib.auth import get_user_model; U=get_user_model(); print('SUPERUSERS=',U.objects.filter(is_superuser=True).count())"

# H) LIMPIAR SQLITE POR SI QUEDÓ
echo ""
echo "=== PASO 9: Limpiando SQLite residual (si existe) ==="
docker compose -f docker-compose.prod.yml exec web sh -c "rm -f /app/db.sqlite3 || true"

echo ""
echo "=========================================="
echo "✅ DESPLIEGUE COMPLETADO"
echo "=========================================="
echo ""
echo "Próximos pasos:"
echo "1. Ejecutar auditoría: ./auditoria_sistema.sh"
echo "2. Acceder al panel admin: http://tu-servidor:8000/admin/"
echo ""