# ⚡ SGIR - Deploy Rápido (10 Minutos)

## 🧭 FASE 0 — Requisitos Previos

✅ **VPS** con Ubuntu 22.04/24.04
✅ **IP pública** anotada
✅ **Dominio** (ej: misgir.com)
✅ **DNS configurado** → Registro A apuntando a IP del VPS

---

## 🚀 FASE 1 — Conectar al VPS

```bash
ssh root@TU_IP_VPS
```

---

## 🐳 FASE 2 — Instalar Docker

```bash
apt update && apt upgrade -y
apt install -y docker.io docker-compose-plugin git
systemctl enable docker && systemctl start docker
```

**Verificar:**
```bash
docker --version
docker compose version
```

---

## 📦 FASE 3 — Clonar Proyecto

```bash
cd /opt
git clone https://github.com/KaradyGamer/Sistema-de-Gesti-n-Integral-para-Restaurantes-SGIR- sgir
cd sgir/restaurante_qr_project
```

---

## 🔐 FASE 4 — Configurar .env

```bash
cp .env.example .env
nano .env
```

**Pegar y ajustar:**

```env
# === DJANGO ===
SECRET_KEY=CLAVE_LARGA_Y_MUY_SECRETA_50_CARACTERES_MINIMO
DEBUG=False
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com

# === BD ===
DB_ENGINE=postgres
POSTGRES_DB=sgir_prod
POSTGRES_USER=sgir_prod_user
POSTGRES_PASSWORD=PASSWORD_MUY_FUERTE
POSTGRES_HOST=db
POSTGRES_PORT=5432

# === CORS/CSRF ===
CORS_ALLOWED_ORIGINS=https://tu-dominio.com,https://www.tu-dominio.com
CSRF_TRUSTED_ORIGINS=https://tu-dominio.com,https://www.tu-dominio.com

# === COOKIES ===
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# === JWT ===
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=20160
```

**Guardar:** `Ctrl+O` → Enter → `Ctrl+X`

---

## 🐘 FASE 5 — Levantar Backend

```bash
docker compose up --build -d
```

**Verificar:**
```bash
docker compose ps
docker compose logs --tail=50 web
```

---

## 🗄️ FASE 6 — Configurar Django

```bash
# Migraciones
docker compose exec web python manage.py migrate

# Crear superusuario
docker compose exec web python manage.py createsuperuser

# Archivos estáticos
docker compose exec web python manage.py collectstatic --noinput
```

---

## 🔒 FASE 7 — HTTPS Automático con Caddy

```bash
apt install -y caddy
nano /etc/caddy/Caddyfile
```

**Pegar:**
```
tu-dominio.com {
    reverse_proxy localhost:8000
}
```

**Reiniciar:**
```bash
systemctl restart caddy
systemctl status caddy --no-pager
```

---

## 🔥 FASE 8 — Firewall

```bash
ufw allow OpenSSH
ufw allow 80
ufw allow 443
ufw enable
ufw status
```

---

## ✅ FASE 9 — Verificación

**En el navegador:**
- https://tu-dominio.com/ → Debe cargar
- https://tu-dominio.com/admin/ → Panel admin
- https://tu-dominio.com/health/ → `{"status":"healthy"}`

**En el VPS:**
```bash
curl https://tu-dominio.com/health/
```

---

## 🛟 FASE 10 — Backups Automáticos

```bash
chmod +x scripts/backup.sh

# Configurar cron (diario 3 AM)
crontab -e
```

**Agregar:**
```
0 3 * * * /opt/sgir/restaurante_qr_project/scripts/backup.sh >> /var/log/sgir_backup.log 2>&1
```

---

## 🎯 Comandos Útiles

```bash
# Ver logs en tiempo real
docker compose logs -f web

# Reiniciar servicios
docker compose restart

# Actualizar código
cd /opt/sgir/restaurante_qr_project
git pull
docker compose up --build -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py collectstatic --noinput

# Backup manual
./scripts/backup.sh

# Acceder a PostgreSQL
docker compose exec db psql -U sgir_prod_user sgir_prod
```

---

## 🚨 Troubleshooting

### Error: "502 Bad Gateway"

```bash
docker compose logs web
docker compose restart web
```

### Error: "CSRF verification failed"

Verificar en `.env`:
```env
CSRF_TRUSTED_ORIGINS=https://tu-dominio.com
```

Reiniciar:
```bash
docker compose restart web
```

### Caddy no obtiene SSL

Verificar DNS:
```bash
nslookup tu-dominio.com
# Debe mostrar tu IP del VPS
```

Ver logs Caddy:
```bash
journalctl -u caddy -n 50
```

---

## 🏁 RESULTADO FINAL

✅ Backend Django corriendo en PostgreSQL
✅ HTTPS automático con Caddy
✅ Firewall configurado
✅ Backups automáticos diarios
✅ Sistema listo para producción

**🎉 Tu sistema SGIR está en producción!**

---

## 📚 Documentación Completa

- **[DEPLOY.md](DEPLOY.md)** - Guía detallada con todos los pasos
- **[README.md](README.md)** - Información del proyecto
- **[.env.example](.env.example)** - Plantilla de configuración

---

**Versión:** v39.5
**Fecha:** 2025-01-30
