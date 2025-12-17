# 🍽️ SGIR - Sistema de Gestión Integral para Restaurantes

**Sistema completo de gestión para restaurantes con menú QR, gestión de pedidos, control de caja, inventario y reportes**

[![Django](https://img.shields.io/badge/Django-5.1.4-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![Version](https://img.shields.io/badge/Version-39.5-green.svg)](#)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-green.svg)](#)

---

## 📊 ESTADO DEL SISTEMA

**Versión**: v39.5
**Estado**: ✅ **PRODUCTION READY**
**Tests**: ✅ 10/10 pasando
**Cobertura**: 85% backend
**Auditoría BD**: 93/100

---

## 🚀 Quick Start

### Opción 1: Docker (Recomendado para Producción)

```bash
# 1. Clonar repositorio
git clone https://github.com/KaradyGamer/Sistema-de-Gesti-n-Integral-para-Restaurantes-SGIR-.git
cd Sistema-de-Gesti-n-Integral-para-Restaurantes-SGIR-/restaurante_qr_project

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env y cambiar DB_ENGINE=postgres

# 3. Levantar servicios
docker compose up --build -d

# 4. Crear superusuario
docker compose exec web python manage.py createsuperuser

# 5. Acceder
# http://localhost:8000
```

### Opción 2: Local (Desarrollo)

```bash
# 1. Crear entorno virtual
python -m venv env
env\Scripts\activate  # Windows
source env/bin/activate  # Linux/Mac

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar .env
cp .env.example .env
# Dejar DB_ENGINE=sqlite para desarrollo

# 4. Migrar base de datos
python manage.py migrate

# 5. Crear superusuario
python manage.py createsuperuser

# 6. Correr servidor
python manage.py runserver
```

---

## 📋 Características Principales

### 🔐 Sistema de Autenticación Multi-Modal

**3 métodos de login independientes:**

| Método | Usuarios | Endpoint | Características |
|--------|----------|----------|-----------------|
| **Password** | Admins, Gerentes | `/staff/login/` | Panel AdminUX |
| **PIN** | Cajeros | `POST /usuarios/login-pin/` | 4-6 dígitos, rate limiting |
| **QR Code** | Meseros, Cocineros | `POST /usuarios/login-qr/` | Tokens 24h, un solo uso |

**Seguridad:**
- ✅ Rate limiting: 5 intentos, 5 minutos bloqueo
- ✅ JWT tokens con refresh automático
- ✅ Validación dual de usuarios activos
- ✅ Soft delete en modelos críticos

---

### 📱 Módulos del Sistema

#### 🛒 **Pedidos y Menú QR**
- Cliente escanea QR → Ve menú → Agrega productos → Confirma pedido
- Pedido aparece automáticamente en cocina
- Estados: Pendiente → En preparación → Listo → Entregado
- Sistema de pago parcial por producto

#### 👨‍🍳 **Panel de Cocina**
- Vista en tiempo real de pedidos pendientes
- Actualización de estados de preparación
- Notificaciones automáticas a meseros

#### 🍽️ **Panel de Mesero**
- Gestión de pedidos por mesa
- Sistema de reservas con validación de solapamiento
- Entrega de pedidos listos
- Solicitud de cuenta a caja

#### 💰 **Módulo de Caja**
- **Jornada Laboral**: Apertura/cierre con validación
- **Pagos múltiples**: Efectivo, Tarjeta, QR, Móvil, Mixto
- **Pago parcial**: Por producto individual
- **Alertas automáticas**: Stock bajo/agotado
- **Cierre de caja**: Por turno con cuadre

#### 🎨 **AdminUX (Panel Administrativo)**
- Dashboard con KPIs en tiempo real
- CRUD completo: Productos, Categorías, Mesas, Usuarios, Reservas
- Diseño Dark Theme profesional
- Generación de QR para usuarios bajo demanda
- Configuración centralizada del sistema

#### 📦 **Inventario**
- Gestión de insumos con categorías
- Control de stock con alertas
- Historial de movimientos (entrada/salida/ajuste)
- Múltiples unidades de medida

#### 📊 **Reportes**
- Ventas por rango de fechas
- Top productos más vendidos
- Métodos de pago utilizados
- Historial de cierres de caja
- Alertas de stock

---

## 🏗️ Arquitectura Técnica

### Stack Tecnológico

**Backend:**
- Django 5.1.4
- Django REST Framework 3.15.2
- JWT Authentication
- PostgreSQL 16 / SQLite (dual)
- Gunicorn 23.0.0

**Frontend:**
- Vanilla JavaScript
- CSS3 Dark Theme (2411 líneas)
- Chart.js para gráficas
- Boxicons

**DevOps:**
- Docker + Docker Compose
- WhiteNoise para estáticos
- Health checks en PostgreSQL

### 10 Aplicaciones Django

| App | Modelos | Propósito |
|-----|---------|-----------|
| **usuarios** | Usuario, QRToken | Autenticación multi-modal |
| **mesas** | Mesa | Gestión de mesas con QR |
| **productos** | Producto, Categoria | Catálogo con control de stock |
| **pedidos** | Pedido, DetallePedido | Sistema de comandas y pago parcial |
| **caja** | JornadaLaboral, Transaccion, CierreCaja, AlertaStock | Módulo financiero completo |
| **inventario** | Insumo, CategoriaInsumo, MovimientoInsumo | Control de insumos |
| **reservas** | Reserva | Sistema de reservaciones |
| **reportes** | ReporteVentas, AnalisisProducto | Business Intelligence |
| **configuracion** | ConfiguracionSistema | Configuración global (Singleton) |
| **adminux** | - | Panel administrativo orquestador |

### Base de Datos

- **Total modelos**: 18
- **Relaciones**: 27 ForeignKeys verificadas
- **Integridad**: 95/100
- **Soft delete**: Usuario, Producto, Categoria, Mesa
- **Protecciones**: PROTECT en relaciones críticas

---

## 🐳 Docker

### Arquitectura de Servicios

```
┌─────────────────────────────────────┐
│      Docker Network (sgir_network)  │
│                                     │
│  ┌──────────┐      ┌─────────────┐ │
│  │   web    │─────▶│     db      │ │
│  │ Django   │      │ PostgreSQL  │ │
│  │ :8000    │      │ :5432       │ │
│  └──────────┘      └─────────────┘ │
│       │                   │         │
│       ▼                   ▼         │
│  ┌────────┐         ┌──────────┐   │
│  │ media/ │         │  pgdata  │   │
│  │ logs/  │         │ (volume) │   │
│  └────────┘         └──────────┘   │
└─────────────────────────────────────┘
```

### Comandos Útiles

```bash
# Levantar servicios
docker compose up -d

# Ver logs
docker compose logs -f web

# Ejecutar comandos Django
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py collectstatic --noinput

# Acceder a PostgreSQL
docker compose exec db psql -U sgir_user -d sgir

# Detener servicios
docker compose down

# Eliminar volúmenes (¡CUIDADO!)
docker compose down -v
```

---

## 🔧 Configuración

### Variables de Entorno (.env)

```env
# Seguridad
SECRET_KEY=tu_clave_super_secreta_y_larga

# Modo
DEBUG=False  # True para desarrollo
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com

# Base de datos (sqlite o postgres)
DB_ENGINE=postgres
POSTGRES_DB=sgir_prod
POSTGRES_USER=sgir_user
POSTGRES_PASSWORD=password_super_seguro
POSTGRES_HOST=db
POSTGRES_PORT=5432

# CORS/CSRF
CORS_ALLOWED_ORIGINS=https://tu-dominio.com
CSRF_TRUSTED_ORIGINS=https://tu-dominio.com

# Cookies (True en producción con HTTPS)
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

---

## 📚 API Endpoints

### Autenticación

- `POST /staff/login/` - Login staff (password)
- `POST /usuarios/login-pin/` - Login cajeros (PIN)
- `POST /usuarios/login-qr/` - Login meseros/cocineros (QR)
- `POST /api/refresh/` - Refrescar JWT token

### Productos

- `GET /api/productos/` - Listar productos
- `POST /api/productos/` - Crear producto (admin)
- `PUT /api/productos/<id>/` - Actualizar producto (admin)
- `DELETE /api/productos/<id>/` - Soft delete (admin)

### Pedidos

- `POST /api/pedidos/cliente/crear/` - Crear pedido (cliente)
- `GET /api/pedidos/cocina/` - Pedidos en cocina
- `GET /api/pedidos/mesero/` - Pedidos por mesa
- `PUT /api/pedidos/<id>/actualizar/` - Actualizar estado

### Caja

- `POST /api/caja/jornada/iniciar/` - Iniciar jornada (cajero)
- `POST /api/caja/jornada/finalizar/` - Finalizar jornada (cajero)
- `GET /api/caja/jornada/` - Estado de jornada
- `POST /api/caja/transacciones/` - Crear transacción
- `GET /api/caja/alertas/` - Alertas de stock

### Reportes

- `GET /api/reportes/ventas/` - Ventas por período
- `GET /api/reportes/productos/top/` - Top productos
- `GET /api/caja/cierres/` - Historial de cierres

---

## 🧪 Testing

```bash
# Correr todos los tests
pytest

# Tests específicos
pytest app/usuarios/tests/test_auth.py -v
pytest app/caja/tests/test_jornada.py -v
pytest app/pedidos/tests/test_pedidos.py -v

# Con coverage
pytest --cov=app --cov-report=html
```

**Estado actual:**
- ✅ 10/10 tests críticos pasando
- ✅ Cobertura: 85% backend
- ✅ Rate limiting verificado
- ✅ Autenticación multi-modal verificada
- ✅ Jornada laboral verificada

---

## 📖 Documentación Adicional

- **[AUDITORIA_BASE_DATOS.md](../AUDITORIA_BASE_DATOS.md)**: Auditoría completa de BD (93/100)
- **[.env.example](.env.example)**: Plantilla de configuración completa

---

## 🔒 Seguridad

### Implementado

- ✅ Rate limiting en autenticación (5 intentos / 5 min)
- ✅ CSRF protection
- ✅ JWT con refresh tokens
- ✅ Validación dual de usuarios activos
- ✅ Soft delete en modelos críticos
- ✅ HttpOnly cookies
- ✅ Permisos por rol en endpoints
- ✅ Validación de jornada laboral (middleware)

### Para Producción

- [ ] Configurar HTTPS (Nginx/Caddy)
- [ ] `DEBUG=False`
- [ ] `SESSION_COOKIE_SECURE=True`
- [ ] `CSRF_COOKIE_SECURE=True`
- [ ] Configurar backups automáticos de PostgreSQL
- [ ] Limitar acceso a puertos (solo 80/443 públicos)

---

## 📊 Roadmap

### v40.0 (Frontend)
- [ ] Sincronizar UI de Reportes con datos reales (actualmente 30%)
- [ ] CRUD de Transacciones en AdminUX
- [ ] UI para MovimientoInsumo
- [ ] Exportación de reportes a Excel/PDF

### Futuras Mejoras
- [ ] Aumentar cobertura de tests a 95%+
- [ ] API documentation con Swagger/ReDoc
- [ ] Caché con Redis
- [ ] Monitoreo con Sentry
- [ ] PWA para meseros/cocineros

---

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama: `git checkout -b feature/nueva-funcionalidad`
3. Commit: `git commit -m 'feat: agregar nueva funcionalidad'`
4. Push: `git push origin feature/nueva-funcionalidad`
5. Abre un Pull Request

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT.

---

## 👥 Autores

- **Desarrollador Principal**: [KaradyGamer](https://github.com/KaradyGamer)

---

## 🆘 Soporte

Si encuentras problemas:
1. Revisa logs: `docker compose logs -f`
2. Verifica estado: `docker compose ps`
3. Ejecuta: `python manage.py check`
4. Abre un [Issue](https://github.com/KaradyGamer/Sistema-de-Gesti-n-Integral-para-Restaurantes-SGIR-/issues)

---

**⭐ Si este proyecto te fue útil, considera darle una estrella en GitHub**
