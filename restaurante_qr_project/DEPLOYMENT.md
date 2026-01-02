# 🚀 DEPLOYMENT.md - SGIR Backend

**Proyecto:** Sistema de Gestión Integral para Restaurantes (SGIR)
**Stack:** Django 5.1.4 + PostgreSQL 16 + Docker
**Última actualización:** 2025-01-02

---

## 📋 Índice

1. [Requisitos Previos](#requisitos-previos)
2. [Despliegue Local (Desarrollo)](#despliegue-local-desarrollo)
3. [Despliegue con Docker](#despliegue-con-docker)
4. [Despliegue en Producción](#despliegue-en-producción)
5. [Configuración de Nginx](#configuración-de-nginx)
6. [Variables de Entorno](#variables-de-entorno)
7. [Migraciones y Datos Iniciales](#migraciones-y-datos-iniciales)
8. [Troubleshooting](#troubleshooting)

---

## 📦 Requisitos Previos

### Software Necesario

**Desarrollo:**
- Python 3.12+
- PostgreSQL 16+ (o SQLite para pruebas)
- Git
- pip / virtualenv

**Producción:**
- Docker 24.0+
- Docker Compose 2.20+
- Nginx 1.24+ (reverse proxy)
- Certificado SSL/TLS

### Verificación Rápida

```bash
python --version        # >= 3.12
docker --version        # >= 24.0
docker compose version  # >= 2.20
psql --version          # >= 16 (si no usas Docker)
```

---

## 💻 Despliegue Local (Desarrollo)

### 1. Clonar Repositorio

```bash
git clone https://github.com/tu-usuario/sgir-backend.git
cd sgir-backend/restaurante_qr_project
```

### 2. Crear Entorno Virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar .env con tus valores
# Mínimo cambiar:
# - SECRET_KEY (generar nueva)
# - DEBUG=True (solo desarrollo)
```

**Generar SECRET_KEY:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 5. Ejecutar Migraciones

```bash
python manage.py migrate
```

### 6. Crear Superusuario

```bash
python manage.py createsuperuser
```

### 7. Cargar Datos Iniciales (Opcional)

```bash
python scripts/crear_datos_iniciales.py
```

### 8. Ejecutar Servidor de Desarrollo

```bash
python manage.py runserver
```

**Acceder a:**
- Frontend: http://localhost:8000/
- Admin: http://localhost:8000/admin/
- API: http://localhost:8000/api/

---

## 🐳 Despliegue con Docker

### Modo Desarrollo

```bash
cd restaurante_qr_project

# Levantar servicios
docker compose up -d

# Ver logs
docker compose logs -f web

# Ejecutar migraciones
docker compose exec web python manage.py migrate

# Crear superusuario
docker compose exec web python manage.py createsuperuser

# Cargar datos iniciales
docker compose exec web python scripts/crear_datos_iniciales.py
```

**Acceder a:**
- http://localhost:8000/

**Detener servicios:**
```bash
docker compose down
```

### Modo Producción

```bash
# Usar archivo de producción
docker compose -f docker-compose.prod.yml up -d

# Recolectar archivos estáticos
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Aplicar migraciones
docker compose -f docker-compose.prod.yml exec web python manage.py migrate

# Crear superusuario
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

---

## ☁️ Despliegue en Producción

### Preparación Pre-Despliegue

**1. Revisar SECURITY.md:**
```bash
cat SECURITY.md
```

**2. Completar CHECKLIST_CLOUD.md:**
```bash
cat CHECKLIST_CLOUD.md
```

**3. Configurar Variables de Entorno:**

Crear archivo `.env` en el servidor con valores de producción:

```bash
SECRET_KEY=<generar-nueva-key-aleatoria>
DEBUG=False
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com

DB_ENGINE=postgres
POSTGRES_DB=sgir_prod
POSTGRES_USER=sgir_prod_user
POSTGRES_PASSWORD=<password-super-seguro>
POSTGRES_HOST=db
POSTGRES_PORT=5432

CORS_ALLOWED_ORIGINS=https://tu-dominio.com
CSRF_TRUSTED_ORIGINS=https://tu-dominio.com

SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### Despliegue en VPS/Cloud

#### Opción 1: Docker Compose (Recomendado)

```bash
# En el servidor
git clone https://github.com/tu-usuario/sgir-backend.git
cd sgir-backend/restaurante_qr_project

# Configurar .env
nano .env

# Levantar producción
docker compose -f docker-compose.prod.yml up -d

# Aplicar migraciones
docker compose -f docker-compose.prod.yml exec web python manage.py migrate

# Recolectar estáticos
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Crear superusuario
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

#### Opción 2: Systemd (Sin Docker)

**1. Instalar dependencias del sistema:**
```bash
sudo apt update
sudo apt install python3.12 python3.12-venv postgresql nginx
```

**2. Configurar PostgreSQL:**
```bash
sudo -u postgres psql
CREATE DATABASE sgir_prod;
CREATE USER sgir_prod_user WITH PASSWORD 'password_seguro';
GRANT ALL PRIVILEGES ON DATABASE sgir_prod TO sgir_prod_user;
\q
```

**3. Configurar aplicación:**
```bash
cd /opt/sgir
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

# Migrar
python manage.py migrate

# Recolectar estáticos
python manage.py collectstatic --noinput
```

**4. Crear servicio systemd:**

`/etc/systemd/system/sgir.service`:
```ini
[Unit]
Description=SGIR Backend
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/sgir/restaurante_qr_project
Environment="PATH=/opt/sgir/venv/bin"
EnvironmentFile=/opt/sgir/restaurante_qr_project/.env
ExecStart=/opt/sgir/venv/bin/gunicorn \
    --workers 4 \
    --bind 0.0.0.0:8000 \
    --access-logfile /var/log/sgir/access.log \
    --error-logfile /var/log/sgir/error.log \
    backend.wsgi:application

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**5. Iniciar servicio:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable sgir
sudo systemctl start sgir
sudo systemctl status sgir
```

---

## 🔧 Configuración de Nginx

### Como Reverse Proxy (Recomendado)

`/etc/nginx/sites-available/sgir`:

```nginx
upstream sgir_backend {
    server localhost:8000;
}

server {
    listen 80;
    server_name tu-dominio.com www.tu-dominio.com;

    # Redirigir a HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name tu-dominio.com www.tu-dominio.com;

    # SSL
    ssl_certificate /etc/letsencrypt/live/tu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tu-dominio.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Headers de seguridad
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Tamaño máximo de upload
    client_max_body_size 20M;

    # Archivos estáticos
    location /static/ {
        alias /opt/sgir/restaurante_qr_project/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /opt/sgir/restaurante_qr_project/media/;
        expires 7d;
    }

    # Proxy al backend
    location / {
        proxy_pass http://sgir_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Healthcheck
    location /health/ {
        proxy_pass http://sgir_backend/health/;
        access_log off;
    }
}
```

**Activar configuración:**
```bash
sudo ln -s /etc/nginx/sites-available/sgir /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Obtener Certificado SSL (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com
sudo certbot renew --dry-run
```

---

## 🔑 Variables de Entorno

### Variables Críticas

| Variable | Desarrollo | Producción | Descripción |
|----------|------------|------------|-------------|
| `DEBUG` | `True` | `False` | Modo debug |
| `SECRET_KEY` | Cualquiera | **Aleatoria única** | Clave secreta Django |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | `tu-dominio.com` | Hosts permitidos |
| `DB_ENGINE` | `sqlite` | `postgres` | Motor de BD |
| `SESSION_COOKIE_SECURE` | `False` | `True` | Cookies solo HTTPS |
| `CSRF_COOKIE_SECURE` | `False` | `True` | CSRF solo HTTPS |

### Variables Opcionales

| Variable | Default | Descripción |
|----------|---------|-------------|
| `JWT_ACCESS_TOKEN_LIFETIME` | `60` | Minutos de vida del token |
| `JWT_REFRESH_TOKEN_LIFETIME` | `20160` | Minutos refresh (14 días) |

---

## 🗄️ Migraciones y Datos Iniciales

### Aplicar Migraciones

```bash
# Local
python manage.py migrate

# Docker
docker compose exec web python manage.py migrate

# Producción
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
```

### Verificar Estado de Migraciones

```bash
python manage.py showmigrations
python manage.py migrate --plan
```

### Crear Datos Iniciales

```bash
# Script personalizado
python scripts/crear_datos_iniciales.py

# O manualmente desde shell
python manage.py shell
```

---

## 🔍 Troubleshooting

### Problema: "DisallowedHost at /"

**Causa:** `ALLOWED_HOSTS` no incluye el dominio.

**Solución:**
```python
# .env
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com,localhost
```

### Problema: "OperationalError: FATAL: password authentication failed"

**Causa:** Credenciales incorrectas de PostgreSQL.

**Solución:**
```bash
# Verificar credenciales en .env
POSTGRES_USER=tu_usuario
POSTGRES_PASSWORD=tu_password

# Recrear usuario en PostgreSQL
sudo -u postgres psql
DROP USER IF EXISTS tu_usuario;
CREATE USER tu_usuario WITH PASSWORD 'tu_password';
GRANT ALL PRIVILEGES ON DATABASE sgir_prod TO tu_usuario;
```

### Problema: "Static files not found (404)"

**Causa:** `collectstatic` no ejecutado.

**Solución:**
```bash
python manage.py collectstatic --noinput
```

### Problema: "502 Bad Gateway" en Nginx

**Causa:** Backend no está corriendo o Nginx no puede conectar.

**Solución:**
```bash
# Verificar que el backend esté corriendo
sudo systemctl status sgir

# Verificar logs
sudo journalctl -u sgir -f

# Verificar conectividad
curl http://localhost:8000/health/
```

### Problema: "CSRF verification failed"

**Causa:** CSRF_TRUSTED_ORIGINS no incluye el dominio.

**Solución:**
```python
# .env
CSRF_TRUSTED_ORIGINS=https://tu-dominio.com,https://www.tu-dominio.com
```

---

## 📊 Monitoreo Post-Despliegue

### Healthcheck

```bash
curl https://tu-dominio.com/health/
# Esperado: {"status":"healthy","timestamp":...}
```

### Logs en Tiempo Real

```bash
# Docker
docker compose logs -f web

# Systemd
sudo journalctl -u sgir -f

# Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Verificar Endpoints Críticos

```bash
# Admin
curl -I https://tu-dominio.com/admin/

# API
curl -I https://tu-dominio.com/api/

# Healthcheck
curl https://tu-dominio.com/health/
```

---

## 🔄 Actualización del Sistema

### Proceso de Actualización

```bash
# 1. Backup de BD
docker compose exec db pg_dump -U $POSTGRES_USER $POSTGRES_DB > backup_$(date +%Y%m%d).sql

# 2. Pull cambios
git pull origin main

# 3. Reconstruir imagen
docker compose -f docker-compose.prod.yml build

# 4. Aplicar migraciones
docker compose -f docker-compose.prod.yml exec web python manage.py migrate

# 5. Recolectar estáticos
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# 6. Reiniciar servicios
docker compose -f docker-compose.prod.yml restart web
```

---

## 📚 Referencias

- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Docker Documentation](https://docs.docker.com/)

---

**Mantenido por:** Equipo SGIR
**Soporte técnico:** deploy@sgir.com