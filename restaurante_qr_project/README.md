# 🍽️ SGIR - Sistema de Gestión Integral para Restaurantes
**Sistema completo de gestión para restaurantes con menú QR, gestión de pedidos, control de caja, inventario y reportes**

[![Django](https://img.shields.io/badge/Django-5.1.4-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![Version](https://img.shields.io/badge/Version-38.8-blue.svg)](#)
[![Status](https://img.shields.io/badge/Status-ALPHA-orange.svg)](#)
[![Audit](https://img.shields.io/badge/Audit-Complete-green.svg)](AUDIT_REPORT.md)

---

## ⚠️ ESTADO DEL SISTEMA

**Versión**: v38.8
**Estado**: ALPHA - En desarrollo activo
**Producción**: ❌ NO LISTO - Ver [AUDIT_REPORT.md](AUDIT_REPORT.md)

### Auditoría de Seguridad (2025-11-12)
- 🔴 **6 Problemas GRAVES** - Requieren acción inmediata
- 🟡 **7 Problemas SUAVES** - Afectan calidad/mantenibilidad
- 🟢 **7 Mejoras PASABLES** - Opcionales

**Ver**: [AUDIT_REPORT.md](AUDIT_REPORT.md) para análisis completo.

---

## 📋 Características Principales

### 🔐 Sistema de Autenticación Multi-Modal

**4 métodos de login independientes:**

| Método | Usuarios | Ruta | Características |
|--------|----------|------|-----------------|
| **Usuario/Contraseña** | Todos | `/login/` | Redirección inteligente |
| **Staff Login** | Personal | `/staff/login/` | Panel AdminUX (Tailwind) |
| **PIN** | Cajeros | `/api/usuarios/login-pin/` | 4-6 dígitos, rate limiting |
| **QR Code** | Meseros/Cocineros | `/qr-login/<token>/` | Tokens 24h, uso único |

**Redirección inteligente**:
- `is_superuser=True` → `/admin/` (Django admin nativo)
- `is_staff=True` → `/adminux/` (Panel moderno)
- Usuario normal → `/menu/` (Menú cliente)

---

### 📱 Menú QR para Clientes
- Escaneo de QR desde mesa
- Catálogo de productos con imágenes
- Carrito de compras interactivo
- Pedidos sin registro

### 👨‍🍳 Panel de Cocina
- Vista en tiempo real de pedidos
- Estados: Pendiente → En preparación → Listo
- Notificaciones automáticas

### 🍽️ Panel de Mesero
- Gestión de pedidos por mesa
- Entrega de pedidos listos
- Sistema de reservas

### 💰 Módulo de Caja
- Apertura/cierre de jornada
- Pagos: efectivo, tarjeta, QR, móvil, mixto
- **Sistema de alertas de stock**
- Control de inventario en tiempo real

### 🎨 Panel AdminUX
- Dashboard con KPIs
- CRUD completo
- **Diseño monocromático** (blanco/negro)
- Modo claro/oscuro
- Accesible (WCAG AAA)

### 📊 Reportes
- Métricas en tiempo real
- Ventas por período
- Productos más vendidos
- Análisis de categorías

---

## 🏗️ Arquitectura

### 8 Aplicaciones Django

| App | Propósito |
|-----|-----------|
| **usuarios** | Autenticación multi-modal |
| **mesas** | Control de mesas con QR |
| **productos** | Inventario y catálogo |
| **pedidos** | Sistema de comandas |
| **caja** | Módulo financiero |
| **reservas** | Reservaciones |
| **reportes** | Business Intelligence |
| **adminux** | Panel administrativo |

---

## 🛠️ Tecnologías

**Backend**: Django 5.1.4, DRF 3.16+, SimpleJWT, SQLite/PostgreSQL
**Frontend**: HTML5, CSS3, JavaScript, Tailwind CSS, jQuery
**Seguridad**: Rate limiting, CSRF, Tokens QR 24h

---

## 🚀 Instalación

### 1. Clonar repositorio
```bash
git clone https://github.com/KaradyGamer/Sistema-de-Gesti-n-Integral-para-Restaurantes-SGIR-.git
cd restaurante_qr_project
```

### 2. Crear entorno virtual
```bash
python -m venv env
env\Scripts\activate  # Windows
source env/bin/activate  # Linux/Mac
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar `.env`

⚠️ **IMPORTANTE**: No usar el `.env` de ejemplo en producción.

```bash
copy .env.example .env  # Windows
```

**Generar SECRET_KEY**:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 5. Aplicar migraciones
```bash
python manage.py migrate
```

### 6. Crear superusuario
```bash
python manage.py createsuperuser
```

### 7. (Opcional) Datos de prueba
```bash
python scripts/crear_datos_iniciales.py
```

**Credenciales**:
- Admin: `admin` / `admin123`
- Cajero1: PIN `1000`
- Mesero1/Cocinero1: Login QR

### 8. Iniciar servidor
```bash
python manage.py runserver
```

**Acceder**:
- Login: http://127.0.0.1:8000/login/
- Staff: http://127.0.0.1:8000/staff/login/
- Admin: http://127.0.0.1:8000/admin/
- AdminUX: http://127.0.0.1:8000/adminux/

---

## 🧪 Tests

❌ **Coverage actual: 0%**

```bash
python manage.py test
```

**Meta**: 70% coverage en 1 mes

---

## 📁 Estructura

```
restaurante_qr_project/
├── app/                    # Apps Django
│   ├── usuarios/           # Autenticación
│   ├── pedidos/            # Pedidos
│   ├── productos/          # Inventario
│   ├── mesas/              # Mesas
│   ├── caja/               # Finanzas
│   ├── reportes/           # BI
│   ├── reservas/           # Reservas
│   └── adminux/            # Panel admin
├── backend/                # Config Django
├── templates/              # HTML + JS/CSS
├── static/                 # Archivos estáticos
├── logs/                   # Logs
├── media/                  # Uploads
├── scripts/                # Utilidades
├── .env                    # Variables (NO en git)
├── AUDIT_REPORT.md         # Auditoría
└── README.md               # Este archivo
```

---

## 🔒 Seguridad

### ⚠️ PROBLEMAS CRÍTICOS

Ver [AUDIT_REPORT.md](AUDIT_REPORT.md) - **6 problemas GRAVES** identificados:

1. SECRET_KEY potencialmente expuesta
2. CSRF_COOKIE_HTTPONLY=False (XSS vulnerable)
3. CORS_ALLOW_ALL_ORIGINS en DEBUG
4. SESSION_SAVE_EVERY_REQUEST sobrecarga BD
5. Falta validación de inputs
6. Middleware sin caché

**Prioridad**: P0 - Resolver AHORA

---

## 📝 Desarrollo

### Scripts útiles
```bash
python manage.py check
python manage.py test --verbosity=2
python scripts/backup_sqlite.py
python scripts/regenerar_qr_empleados.py
```

### Logs en tiempo real
```powershell
Get-Content logs/django.log -Wait -Tail 20
```

---

## 🐛 Problemas Comunes

**CSRF token missing**: Agregar `<meta name="csrf-token">` en template

**Rate limit exceeded**: Esperar 5 min o limpiar cache

**Token QR expirado**: Regenerar desde panel cajero

**Jornada cerrada**: Cajero debe abrir jornada

---

## ✅ Cambios v38.8 (2025-11-12)

**Auditoría**:
- ✅ Análisis completo del sistema
- ✅ 6 problemas GRAVES identificados
- ✅ Plan de acción creado

**Limpieza**:
- ✅ 342 archivos temporales eliminados
- ✅ 4 archivos .md innecesarios borrados
- ✅ README actualizado

**Features**:
- ✅ Diseño monocromático AdminUX
- ✅ Login inteligente con redirección automática
- ✅ Modo claro/oscuro persistente

---

## 📈 Roadmap

### FASE 1: Seguridad (Semana 1) 🔴
- [ ] Rotar SECRET_KEY
- [ ] Fix CSRF HttpOnly
- [ ] Eliminar CORS_ALLOW_ALL
- [ ] Optimizar sesiones
- [ ] Validación con Forms
- [ ] Caché en middleware

### FASE 2: Calidad (Semanas 2-3) 🟡
- [ ] Refactorizar código duplicado
- [ ] Tests (40% coverage)
- [ ] Paginación
- [ ] Logging estandarizado
- [ ] Swagger docs

### FASE 3: Optimización (Semana 4) 🟢
- [ ] Type hints
- [ ] URL reverse()
- [ ] API versioning
- [ ] Rate limiting APIs
- [ ] Monitoreo (Sentry)

---

## ⚠️ DISCLAIMER

**NO USAR EN PRODUCCIÓN** sin resolver problemas críticos.

Riesgos:
- Compromiso de datos
- Pérdida financiera
- Ataques XSS/CSRF
- Degradación de performance

---

## 📄 Licencia

Proyecto privado y confidencial.

---

## 👥 Contacto

**GitHub**: https://github.com/KaradyGamer/Sistema-de-Gesti-n-Integral-para-Restaurantes-SGIR-

**Docs**: [AUDIT_REPORT.md](AUDIT_REPORT.md)

---

**Versión**: 38.8
**Actualización**: 2025-11-12
**Estado**: ALPHA
**Tests**: 0% coverage
**Auditoría**: ✅ Completada
