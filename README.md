# 🍽️ SGIR - Sistema de Gestión Integral para Restaurantes

[![Django](https://img.shields.io/badge/Django-5.1.4-green)](https://www.djangoproject.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue)](https://docs.docker.com/compose/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)](https://www.postgresql.org/)
[![n8n](https://img.shields.io/badge/n8n-Automation-orange)](https://n8n.io/)
[![Version](https://img.shields.io/badge/Version-40.5.1-success)](https://github.com/KaradyGamer/Sistema-de-Gesti-n-Integral-para-Restaurantes-SGIR-)

Sistema completo de gestión para restaurantes con módulos de caja, pedidos, inventario, producción, reservas y automatización con n8n.

---

## 📁 Estructura del Repositorio

```
ProyectoR/
├── .claude/                    # Configuración local de Claude Code (NO versionado)
├── restaurante_qr_project/     # Proyecto Django principal
│   ├── app/                    # Aplicaciones Django (11 módulos)
│   ├── backend/                # Configuración del proyecto
│   ├── static/                 # Archivos estáticos
│   ├── templates/              # Templates HTML
│   ├── docker-compose.yml      # Orquestación de contenedores
│   ├── Dockerfile              # Imagen Docker de SGIR
│   ├── .env.example            # Plantilla de variables de entorno
│   ├── SECURITY_SETUP.md       # Guía de seguridad
│   └── README.md               # Documentación del proyecto Django
└── README.md                   # Este archivo
```

### Sobre la carpeta `.claude/`

- Contiene configuración local de Claude Code (IDE settings)
- **NO se versiona** (está en `.gitignore`)
- Cada desarrollador puede tener su propia configuración local

---

## 🚀 Quick Start

### Requisitos Previos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado y corriendo
- Git
- PowerShell (Windows) o Bash (Linux/Mac)

### 1. Clonar el Repositorio

```bash
git clone https://github.com/KaradyGamer/Sistema-de-Gesti-n-Integral-para-Restaurantes-SGIR-.git
cd Sistema-de-Gesti-n-Integral-para-Restaurantes-SGIR-/restaurante_qr_project
```

### 2. Configurar Variables de Entorno

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
notepad .env
```

**Linux/Mac (Bash):**
```bash
cp .env.example .env
nano .env
```

**Editar las variables críticas:**
- `SECRET_KEY`: Generar con `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- `POSTGRES_PASSWORD`: Password seguro (16+ caracteres)
- `N8N_API_KEY`: Generar con `openssl rand -hex 32`
- `N8N_ENCRYPTION_KEY`: Generar con `openssl rand -base64 32`
- `N8N_BASIC_AUTH_PASSWORD`: Password para login n8n
- `QR_HOST`: Tu IP local o dominio

📘 **Ver guía completa:** [SECURITY_SETUP.md](restaurante_qr_project/SECURITY_SETUP.md)

### 3. Levantar los Servicios

```bash
docker compose up -d
```

**Servicios disponibles:**
- **SGIR Backend:** http://localhost:8000
- **n8n Automation:** http://localhost:5678 (usuario: `admin`, password: desde `.env`)

### 4. Verificar Estado

**Windows (PowerShell):**
```powershell
docker compose ps
docker compose logs --tail=50 web
docker compose logs --tail=50 n8n
```

**Linux/Mac (Bash):**
```bash
docker compose ps
docker compose logs --tail=50 web
docker compose logs --tail=50 n8n
```

**Todos los contenedores deben estar `Up` y `healthy`:**
- `sgir_db` (PostgreSQL 16 - SGIR)
- `sgir_web` (Django + Gunicorn)
- `sgir_n8n_db` (PostgreSQL 16 - n8n)
- `sgir_n8n` (n8n Automation Platform)

---

## 🧪 Testing del Sistema

### Health Check Endpoints

**Backend SGIR:**
```bash
# Windows (PowerShell)
Invoke-RestMethod -Uri "http://localhost:8000/health/" -Method Get

# Linux/Mac (Bash)
curl http://localhost:8000/health/
```

**n8n Interface:**
```bash
# Abrir en navegador
http://localhost:5678
```

### API de Integraciones (requiere X-API-KEY)

**Verificar stock bajo:**
```powershell
# Windows (PowerShell)
$headers = @{'X-API-KEY' = 'tu-api-key-desde-env'}
Invoke-RestMethod -Uri "http://localhost:8000/api/integraciones/inventario/stock-bajo/" -Headers $headers
```

```bash
# Linux/Mac (Bash)
curl -H "X-API-KEY: tu-api-key-desde-env" http://localhost:8000/api/integraciones/inventario/stock-bajo/
```

**Resumen de cierres de caja:**
```powershell
# Windows (PowerShell)
Invoke-RestMethod -Uri "http://localhost:8000/api/integraciones/caja/resumen-cierres/?fecha=2025-12-26" -Headers $headers
```

```bash
# Linux/Mac (Bash)
curl -H "X-API-KEY: tu-api-key-desde-env" "http://localhost:8000/api/integraciones/caja/resumen-cierres/?fecha=2025-12-26"
```

---

## 📦 Módulos del Sistema

### Backend Django (11 Apps)

| Módulo | Descripción | Endpoints Principales |
|--------|-------------|----------------------|
| **usuarios** | Gestión de usuarios, roles y QR | `/api/usuarios/`, `/usuarios/login/` |
| **caja** | Registro de transacciones y pagos | `/api/caja/`, `/caja/` |
| **pedidos** | Gestión de pedidos de clientes | `/api/pedidos/`, `/pedidos/` |
| **productos** | Catálogo de productos del menú | `/api/productos/` |
| **inventario** | Control de stock de insumos | `/api/inventario/` |
| **produccion** | Recetas y producción de productos | `/api/produccion/` |
| **mesas** | Gestión de mesas y ubicaciones | `/api/mesas/` |
| **reservas** | Sistema de reservaciones | `/api/reservas/` |
| **reportes** | Reportes y estadísticas | `/api/reportes/` |
| **configuracion** | Configuración del sistema | `/api/configuracion/` |
| **integraciones** | API para n8n y webhooks | `/api/integraciones/` |

### n8n Automation

- **Workflows:** Automatización de tareas repetitivas
- **Webhooks:** Recepción de eventos externos
- **Integraciones:** Conectar con servicios externos (email, SMS, WhatsApp, etc.)

---

## 🔧 Comandos Útiles

### Gestión de Contenedores

**Iniciar servicios:**
```bash
docker compose up -d
```

**Detener servicios:**
```bash
docker compose down
```

**Rebuild completo:**
```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

**Ver logs en tiempo real:**
```bash
docker compose logs -f web
docker compose logs -f n8n
```

### Django Management

**Ejecutar migraciones:**
```bash
docker compose exec web python manage.py migrate
```

**Crear superusuario:**
```bash
docker compose exec web python manage.py createsuperuser
```

**Collectstatic:**
```bash
docker compose exec web python manage.py collectstatic --noinput
```

**Acceder a shell de Django:**
```bash
docker compose exec web python manage.py shell
```

### Base de Datos

**Backup de PostgreSQL (SGIR):**
```bash
docker compose exec db pg_dump -U sgir_user sgir > backup_sgir_$(date +%Y%m%d).sql
```

**Backup de PostgreSQL (n8n):**
```bash
docker compose exec n8n_db pg_dump -U n8n n8n > backup_n8n_$(date +%Y%m%d).sql
```

**Restaurar backup:**
```bash
docker compose exec -T db psql -U sgir_user sgir < backup_sgir_20251226.sql
```

---

## 🔒 Seguridad

### Variables Críticas

⚠️ **NUNCA** subir `.env` al repositorio. Las siguientes variables son críticas:

- `SECRET_KEY` - Clave secreta de Django
- `POSTGRES_PASSWORD` - Password de base de datos
- `N8N_API_KEY` - API key para integraciones
- `N8N_ENCRYPTION_KEY` - Clave de encriptación de n8n
- `N8N_BASIC_AUTH_PASSWORD` - Password de login n8n

### Checklist Pre-Producción

- [ ] `DEBUG=False` en `.env`
- [ ] SECRET_KEY único y rotado
- [ ] Passwords fuertes (16+ caracteres)
- [ ] ALLOWED_HOSTS configurado con dominio real
- [ ] HTTPS habilitado (SSL/TLS)
- [ ] Logs de acceso configurados
- [ ] Backups automáticos programados
- [ ] `.env` NO está en Git (verificar con `git ls-files | grep .env`)

📘 **Guía completa de seguridad:** [SECURITY_SETUP.md](restaurante_qr_project/SECURITY_SETUP.md)

---

## 🐛 Troubleshooting

### Error: "SECRET_KEY not found"

```powershell
# Verificar que .env existe
Test-Path .env

# Copiar desde ejemplo
Copy-Item .env.example .env
```

### Error: "Container sgir_web is restarting"

```bash
# Ver logs del contenedor
docker compose logs --tail=100 web

# Verificar .env tiene todas las variables
docker compose exec web env | grep -E 'SECRET_KEY|POSTGRES'
```

### Error: "CSRF token from header has incorrect length"

```env
# En .env debe estar:
CSRF_COOKIE_HTTPONLY=False
SESSION_COOKIE_HTTPONLY=True
```

### n8n no accesible en localhost:5678

```bash
# Verificar healthcheck
docker compose ps n8n

# Ver logs de n8n
docker compose logs --tail=100 n8n

# Verificar que puerto 5678 no esté ocupado
netstat -ano | findstr :5678
```

### Base de datos no conecta

```bash
# Verificar que db está healthy
docker compose ps db

# Verificar credenciales en .env
docker compose exec db psql -U sgir_user -d sgir

# Resetear volúmenes (⚠️ BORRA DATOS)
docker compose down -v
docker compose up -d
```

---

## 📚 Documentación

- **[README Principal](restaurante_qr_project/README.md)** - Documentación detallada del proyecto Django
- **[SECURITY_SETUP.md](restaurante_qr_project/SECURITY_SETUP.md)** - Guía de seguridad y configuración de .env
- **[Django Documentation](https://docs.djangoproject.com/en/5.0/)** - Documentación oficial de Django
- **[n8n Documentation](https://docs.n8n.io/)** - Documentación oficial de n8n
- **[Docker Compose Documentation](https://docs.docker.com/compose/)** - Documentación oficial de Docker Compose

---

## 🤝 Contribuir

1. Fork el proyecto
2. Crear branch de feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

---

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para más detalles.

---

## 👥 Autores

- **JhamilC** - [GitHub](https://github.com/KaradyGamer)

---

## 🙏 Agradecimientos

- Claude Sonnet 4.5 por asistencia en desarrollo
- Comunidad Django
- Equipo de n8n

---

**🚀 SGIR v40.5.1 - Production Ready**
