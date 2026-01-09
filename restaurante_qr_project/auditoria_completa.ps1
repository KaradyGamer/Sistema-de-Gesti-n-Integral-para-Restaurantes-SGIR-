# ============================================
# AUDITORÍA COMPLETA SGIR - READ-ONLY
# Versión: PowerShell para Windows
# ============================================

Write-Host "=============================="
Write-Host " AUDITORIA TOTAL SGIR (READ-ONLY)"
Write-Host "=============================="

Write-Host "`n== [1] DOCKER PS (estado contenedores) =="
docker compose -f docker-compose.prod.yml ps

Write-Host "`n== [2] HEALTHCHECK (web) =="
docker inspect sgir_web_prod --format "{{json .Config.Healthcheck}}"
docker inspect sgir_web_prod --format "{{json .State.Health}}"

Write-Host "`n== [3] LOGS WEB (ultimas 120 lineas) =="
docker compose -f docker-compose.prod.yml logs --tail=120 web

Write-Host "`n== [4] LOGS DB (ultimas 80 lineas) =="
docker compose -f docker-compose.prod.yml logs --tail=80 db

Write-Host "`n== [5] VARIABLES EN CONTENEDOR WEB (Postgres/SQLite) =="
docker compose -f docker-compose.prod.yml exec web sh -c "env | grep -E 'POSTGRES_|DB_ENGINE|DATABASE_URL|DJANGO|DEBUG' | sort"

Write-Host "`n== [6] DJANGO CHECK =="
docker compose -f docker-compose.prod.yml exec web python manage.py check

Write-Host "`n== [7] DB ENGINE REAL (Django settings) =="
docker compose -f docker-compose.prod.yml exec web python manage.py shell -c "from django.conf import settings; print('ENGINE=',settings.DATABASES['default']['ENGINE']); print('HOST=',settings.DATABASES['default'].get('HOST')); print('NAME=',settings.DATABASES['default'].get('NAME'))"

Write-Host "`n== [8] CONEXION A POSTGRES (si aplica) =="
docker compose -f docker-compose.prod.yml exec web python manage.py shell -c "from django.db import connection; print('VENDOR=',connection.vendor); print('DB_NAME=',connection.settings_dict.get('NAME')); print('DB_HOST=',connection.settings_dict.get('HOST'))"

Write-Host "`n== [9] MIGRACIONES (resumen) =="
docker compose -f docker-compose.prod.yml exec web python manage.py showmigrations --plan | Select-Object -Last 80

Write-Host "`n== [10] TABLAS EN BD (conteo + checks claves) =="
docker compose -f docker-compose.prod.yml exec web python manage.py shell -c "from django.db import connection; t=set(connection.introspection.table_names()); print('TOTAL_TABLAS=',len(t)); print('tiene_usuarios_usuario=',('usuarios_usuario' in t)); print('tiene_django_migrations=',('django_migrations' in t)); print('tiene_auth_permission=',('auth_permission' in t))"

Write-Host "`n== [11] USUARIOS (superusers/staff) =="
docker compose -f docker-compose.prod.yml exec web python manage.py shell -c "from django.contrib.auth import get_user_model; U=get_user_model(); print('TABLA_USER=',U._meta.db_table); print('SUPERUSERS=',U.objects.filter(is_superuser=True).count()); print('STAFF=',U.objects.filter(is_staff=True).count());"

Write-Host "`n== [12] ORM SMOKE TEST (modelos con error) =="
docker compose -f docker-compose.prod.yml exec web python manage.py shell -c "from django.apps import apps; bad=[];
for m in apps.get_models():
    try: m.objects.first()
    except Exception as e: bad.append((m._meta.label, str(e)[:200]));
print('ORM_ERRORS=',bad)"

Write-Host "`n== [13] FRONTEND BASICO (existencia templates/static) =="
docker compose -f docker-compose.prod.yml exec web sh -c "test -d /app/templates && echo 'OK templates existe' || echo 'ERROR templates NO existe'; test -d /app/static && echo 'OK static existe' || echo 'WARN static NO existe (puede ser normal si usas staticfiles)'; test -d /app/staticfiles && echo 'OK staticfiles existe' || echo 'ERROR staticfiles NO existe'"

Write-Host "`n=============================="
Write-Host " FIN AUDITORIA TOTAL"
Write-Host "=============================="