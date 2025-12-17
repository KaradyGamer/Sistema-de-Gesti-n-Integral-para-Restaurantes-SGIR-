# =€ Guía de Deploy SGIR - VPS con Docker

## =Ë Requisitos Previos

-  VPS Ubuntu 22.04/24.04 (DigitalOcean, Hetzner, Vultr, AWS Lightsail)
-  Dominio apuntando a la IP del VPS
-  SSH habilitado
-  Proyecto en repositorio Git

---

## <¯ PASO 1: Conseguir VPS

### Opciones Recomendadas

| Proveedor | Plan Mínimo | Precio | Specs |
|-----------|-------------|--------|-------|
| **DigitalOcean** | Basic Droplet | $6/mes | 1 vCPU, 1GB RAM, 25GB SSD |
| **Hetzner** | CX11 | ¬4/mes | 1 vCPU, 2GB RAM, 20GB SSD |
| **Vultr** | Regular Cloud | $6/mes | 1 vCPU, 1GB RAM, 25GB SSD |
| **AWS Lightsail** | $3.50/mes | $3.50/mes | 512MB RAM, 1 vCPU, 20GB SSD |

### Crear VPS (Ejemplo DigitalOcean)

1. **Ir a**: https://www.digitalocean.com/
2. **Create** ’ **Droplets**
3. **Seleccionar**:
   - **OS**: Ubuntu 22.04 LTS
   - **Plan**: Basic ($6/mes)
   - **Datacenter**: Más cercano a tus usuarios
   - **Authentication**: SSH Key (recomendado) o Password
4. **Create Droplet**
5. **Anotar IP pública**: `XXX.XXX.XXX.XXX`

---

## = PASO 2: Conectarse por SSH

Desde tu PC:

```bash
ssh root@TU_IP
```

Si usas contraseña, te la pedirá. Si usas SSH key, entrará directo.

---

## =3 PASO 3: Instalar Docker y Docker Compose

En el VPS, ejecuta:

```bash
# Actualizar sistema
apt update -y && apt upgrade -y

# Instalar dependencias
apt install -y ca-certificates curl gnupg git

# Agregar Docker GPG key
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

# Agregar repositorio Docker
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  > /etc/apt/sources.list.d/docker.list

# Instalar Docker
apt update -y
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

**Verificar instalación:**

```bash
docker --version
# Docker version 24.0.x

docker compose version
# Docker Compose version v2.x.x
```

---

## =æ PASO 4: Subir el Proyecto al VPS

### Opción A: Clonar desde Git (Recomendado)

```bash
cd /opt
git clone https://github.com/TU_USUARIO/TU_REPO.git sgir
cd sgir/restaurante_qr_project
```

### Opción B: Transferir con SCP (desde tu PC)

```bash
# Desde tu PC
scp -r restaurante_qr_project root@TU_IP:/opt/sgir/
```

---

## ™ PASO 5: Crear .env de Producción

En el VPS, dentro de `/opt/sgir/restaurante_qr_project/`:

```bash
nano .env
```

**Pegar esta configuración (AJUSTA LOS VALORES):**

```env
# ====================================
# SGIR - Configuración de Producción
# ====================================

# === SEGURIDAD ===
SECRET_KEY=GENERA_UNA_CLAVE_LARGA_Y_ALEATORIA_AQUI_MINIMO_50_CARACTERES

# === MODO ===
DEBUG=False

# === HOSTS PERMITIDOS ===
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com,TU_IP_VPS

# === BASE DE DATOS ===
DB_ENGINE=postgres
POSTGRES_DB=sgir_prod
POSTGRES_USER=sgir_prod_user
POSTGRES_PASSWORD=PASSWORD_MUY_SEGURO_Y_ALEATORIO
POSTGRES_HOST=db
POSTGRES_PORT=5432

# === CORS/CSRF ===
CORS_ALLOWED_ORIGINS=https://tu-dominio.com,https://www.tu-dominio.com
CSRF_TRUSTED_ORIGINS=https://tu-dominio.com,https://www.tu-dominio.com

# === COOKIES SEGURAS (HTTPS) ===
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# === JWT ===
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=20160
```

**Generar SECRET_KEY:**

```bash
docker run --rm python:3.13-slim python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Guardar y salir:**
- `Ctrl + O` ’ Enter (guardar)
- `Ctrl + X` (salir)

---

## =¢ PASO 6: Levantar Backend con Docker

En `/opt/sgir/restaurante_qr_project/`:

```bash
# Construir y levantar servicios
docker compose up --build -d

# Ver estado
docker compose ps
```

**Deberías ver:**

```
NAME                      STATUS         PORTS
sgir_db                   Up (healthy)   0.0.0.0:5432->5432/tcp
sgir_web                  Up             0.0.0.0:8000->8000/tcp
```

**Ejecutar migraciones y crear admin:**

```bash
# Migraciones
docker compose exec web python manage.py migrate

# Colectar archivos estáticos
docker compose exec web python manage.py collectstatic --noinput

# Crear superusuario
docker compose exec web python manage.py createsuperuser
# Username: admin
# Email: tu@email.com
# Password: ********
```

**Verificar que funciona:**

```bash
curl http://localhost:8000
# Debería responder con HTML
```

---

## = PASO 7: HTTPS con Caddy (Automático)

### 7.1 Instalar Caddy

```bash
apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
apt update
apt install caddy
```

### 7.2 Configurar Reverse Proxy

```bash
nano /etc/caddy/Caddyfile
```

**Pegar (REEMPLAZA tu-dominio.com):**

```
tu-dominio.com, www.tu-dominio.com {
    reverse_proxy localhost:8000

    # Headers de seguridad
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        X-XSS-Protection "1; mode=block"
        Referrer-Policy "strict-origin-when-cross-origin"
    }

    # Logs
    log {
        output file /var/log/caddy/access.log
    }
}
```

**Guardar y reiniciar:**

```bash
systemctl restart caddy
systemctl status caddy --no-pager
```

 **Caddy obtiene certificado SSL automáticamente de Let's Encrypt**

---

## =% PASO 8: Configurar Firewall

```bash
# Permitir SSH (IMPORTANTE, no te bloquees)
ufw allow OpenSSH

# Permitir HTTP y HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Habilitar firewall
ufw enable

# Verificar
ufw status
```

**Deberías ver:**

```
Status: active

To                         Action      From
--                         ------      ----
OpenSSH                    ALLOW       Anywhere
80/tcp                     ALLOW       Anywhere
443/tcp                    ALLOW       Anywhere
```

---

## < PASO 9: Apuntar Dominio al VPS

### En tu proveedor de DNS (Cloudflare, Namecheap, GoDaddy, etc.):

**Agregar registros A:**

| Tipo | Nombre | Valor | TTL |
|------|--------|-------|-----|
| A | @ | IP_DE_TU_VPS | Automático |
| A | www | IP_DE_TU_VPS | Automático |

**Ejemplo en Cloudflare:**

1. Dashboard ’ Seleccionar dominio
2. **DNS** ’ **Add record**
3. **Type**: A
4. **Name**: @ (para dominio raíz)
5. **IPv4 address**: IP_DE_TU_VPS
6. **Proxy status**:   **Desactivar** (debe estar en gris, no naranja)
7. **Save**
8. Repetir con **Name**: www

**Esperar propagación DNS (5-30 minutos):**

```bash
# Verificar desde tu PC
nslookup tu-dominio.com
```

---

##  PASO 10: Verificación Final

### 10.1 Verificar Logs

```bash
# Logs de Django
docker compose logs --tail=100 -f web

# Logs de PostgreSQL
docker compose logs --tail=100 db

# Logs de Caddy
tail -f /var/log/caddy/access.log
```

### 10.2 Probar en el Navegador

**Acceder a:**

-  https://tu-dominio.com ’ Debería cargar (con HTTPS)
-  https://tu-dominio.com/admin/ ’ Panel de admin
-  https://tu-dominio.com/adminux/ ’ Panel AdminUX
-  https://www.tu-dominio.com ’ Debería funcionar igual

### 10.3 Verificar SSL

```bash
curl -I https://tu-dominio.com
```

Debería mostrar: `HTTP/2 200` y `server: Caddy`

---

## =' CONFIGURACIONES ADICIONALES

### Auto-start al Reiniciar Servidor

```bash
docker update --restart unless-stopped sgir_web
docker update --restart sgir_db
```

### Backups Automáticos de PostgreSQL

**Crear directorio de backups:**

```bash
mkdir -p /opt/backups
```

**Crear script de backup:**

```bash
nano /opt/backups/backup.sh
```

**Pegar:**

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="sgir_prod"
DB_USER="sgir_prod_user"

cd /opt/sgir/restaurante_qr_project

# Backup de PostgreSQL
docker compose exec -T db pg_dump -U $DB_USER $DB_NAME | gzip > $BACKUP_DIR/sgir_$DATE.sql.gz

# Mantener solo últimos 7 backups
find $BACKUP_DIR -name "sgir_*.sql.gz" -mtime +7 -delete

echo "Backup completado: sgir_$DATE.sql.gz"
```

**Dar permisos:**

```bash
chmod +x /opt/backups/backup.sh
```

**Configurar cron (backup diario a las 3 AM):**

```bash
crontab -e
```

**Agregar:**

```
0 3 * * * /opt/backups/backup.sh >> /var/log/backup.log 2>&1
```

### Monitoreo de Recursos

```bash
# Ver uso de CPU/RAM
docker stats

# Ver espacio en disco
df -h

# Ver logs en tiempo real
docker compose logs -f
```

---

## =¨ Troubleshooting

### Error: "502 Bad Gateway"

**Causa**: Django no está corriendo

**Solución:**

```bash
docker compose ps
docker compose logs web
docker compose restart web
```

### Error: "Connection refused" en PostgreSQL

**Solución:**

```bash
docker compose logs db
docker compose restart db
```

### Error: "CSRF verification failed"

**Causa**: CSRF_TRUSTED_ORIGINS incorrecto

**Solución:**

```bash
nano .env
# Verificar CSRF_TRUSTED_ORIGINS=https://tu-dominio.com
docker compose restart web
```

### Caddy no obtiene certificado SSL

**Causa**: DNS no apunta al VPS

**Verificar:**

```bash
nslookup tu-dominio.com
# Debe mostrar la IP de tu VPS

systemctl status caddy
journalctl -u caddy -n 50
```

### Restaurar backup

```bash
cd /opt/sgir/restaurante_qr_project
gunzip -c /opt/backups/sgir_FECHA.sql.gz | docker compose exec -T db psql -U sgir_prod_user sgir_prod
```

---

## =Ê Comandos Útiles

### Reiniciar servicios

```bash
docker compose restart
```

### Ver logs en tiempo real

```bash
docker compose logs -f web
```

### Actualizar código desde Git

```bash
cd /opt/sgir/restaurante_qr_project
git pull
docker compose up --build -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py collectstatic --noinput
```

### Shell de Django

```bash
docker compose exec web python manage.py shell
```

### Acceder a PostgreSQL

```bash
docker compose exec db psql -U sgir_prod_user sgir_prod
```

---

## <¯ Checklist Final

- [ ] VPS creado y SSH funcionando
- [ ] Docker y Docker Compose instalados
- [ ] Proyecto clonado en `/opt/sgir/`
- [ ] `.env` configurado con valores de producción
- [ ] `docker compose up -d` corriendo
- [ ] Migraciones aplicadas
- [ ] Superusuario creado
- [ ] Caddy instalado y configurado
- [ ] Firewall (UFW) habilitado
- [ ] Dominio apuntando al VPS
- [ ] HTTPS funcionando automáticamente
- [ ] Backups automáticos configurados
- [ ] Auto-restart habilitado

---

## =Þ Soporte por Proveedor

### DigitalOcean
- **Docs**: https://docs.digitalocean.com/
- **Community**: https://www.digitalocean.com/community/

### Hetzner
- **Docs**: https://docs.hetzner.com/
- **Support**: https://accounts.hetzner.com/

### Cloudflare (DNS)
- **Docs**: https://developers.cloudflare.com/dns/
- **Dashboard**: https://dash.cloudflare.com/

---

## ¡ Deploy Alternativo: Railway / Render

Si prefieres un deploy más simple (sin VPS manual):

### Railway.app

```bash
# Instalar CLI
npm i -g @railway/cli

# Login
railway login

# Deploy
railway up
```

### Render.com

1. Conectar repo GitHub
2. Seleccionar **Web Service**
3. Build Command: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
4. Start Command: `gunicorn backend.wsgi:application`
5. Agregar PostgreSQL desde dashboard
6. Configurar variables de entorno

---

**<‰ ¡Tu sistema SGIR está en producción con HTTPS automático!**
