#!/bin/bash
# ============================================
# AUDITORÍA COMPLETA SGIR - READ-ONLY
# Versión: Total con detección de errores
# ============================================

echo "=============================="
echo " AUDITORIA TOTAL SGIR (READ-ONLY)"
echo "=============================="

echo ""
echo "== [1] DOCKER PS (estado contenedores) =="
docker compose -f docker-compose.prod.yml ps

echo ""
echo "== [2] HEALTHCHECK (web) =="
docker inspect sgir_web_prod --format "{{json .Config.Healthcheck}}"
docker inspect sgir_web_prod --format "{{json .State.Health}}"

echo ""
echo "== [3] LOGS WEB (ultimas 120 lineas) =="
docker compose -f docker-compose.prod.yml logs --tail=120 web

echo ""
echo "== [4] LOGS DB (ultimas 80 lineas) =="
docker compose -f docker-compose.prod.yml logs --tail=80 db

echo ""
echo "== [5] VARIABLES EN CONTENEDOR WEB (Postgres/SQLite) =="
docker compose -f docker-compose.prod.yml exec web sh -lc "env | egrep 'POSTGRES_|DB_ENGINE|DATABASE_URL|DJANGO|DEBUG' | sort || true"

echo ""
echo "== [6] DJANGO CHECK =="
docker compose -f docker-compose.prod.yml exec web python manage.py check

echo ""
echo "== [7] DB ENGINE REAL (Django settings) =="
docker compose -f docker-compose.prod.yml exec web python manage.py shell -c "from django.conf import settings; print('ENGINE=',settings.DATABASES['default']['ENGINE']); print('HOST=',settings.DATABASES['default'].get('HOST')); print('NAME=',settings.DATABASES['default'].get('NAME'))"

echo ""
echo "== [8] CONEXION A POSTGRES (si aplica) =="
docker compose -f docker-compose.prod.yml exec web python manage.py shell -c "from django.db import connection; print('VENDOR=',connection.vendor); print('DB_NAME=',connection.settings_dict.get('NAME')); print('DB_HOST=',connection.settings_dict.get('HOST'))"

echo ""
echo "== [9] MIGRACIONES (resumen) =="
docker compose -f docker-compose.prod.yml exec web python manage.py showmigrations --plan | tail -n 80

echo ""
echo "== [10] TABLAS EN BD (conteo + checks claves) =="
docker compose -f docker-compose.prod.yml exec web python manage.py shell -c "from django.db import connection; t=set(connection.introspection.table_names()); print('TOTAL_TABLAS=',len(t)); print('tiene_usuarios_usuario=',('usuarios_usuario' in t)); print('tiene_django_migrations=',('django_migrations' in t)); print('tiene_auth_permission=',('auth_permission' in t))"

echo ""
echo "== [11] USUARIOS (superusers/staff) =="
docker compose -f docker-compose.prod.yml exec web python manage.py shell -c "from django.contrib.auth import get_user_model; U=get_user_model(); print('TABLA_USER=',U._meta.db_table); print('SUPERUSERS=',U.objects.filter(is_superuser=True).count()); print('STAFF=',U.objects.filter(is_staff=True).count());"

echo ""
echo "== [12] ORM SMOKE TEST (modelos con error) =="
docker compose -f docker-compose.prod.yml exec web python manage.py shell -c "from django.apps import apps; bad=[];
for m in apps.get_models():
    try: m.objects.first()
    except Exception as e: bad.append((m._meta.label, str(e)[:200]));
print('ORM_ERRORS=',bad)"

echo ""
echo "== [13] FRONTEND BASICO (existencia templates/static) =="
docker compose -f docker-compose.prod.yml exec web sh -lc "test -d /app/templates && echo 'OK templates existe' || echo 'ERROR templates NO existe'; test -d /app/static && echo 'OK static existe' || echo 'WARN static NO existe (puede ser normal si usas static_collected)'; test -d /app/staticfiles && echo 'OK staticfiles existe' || echo 'ERROR staticfiles NO existe'"

echo ""
echo "=============================="
echo " FIN AUDITORIA TOTAL"
echo "=============================="