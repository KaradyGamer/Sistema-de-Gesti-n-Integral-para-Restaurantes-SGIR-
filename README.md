# 🍽️ SGIR - Sistema de Gestión Integral para Restaurantes

Sistema profesional de gestión para restaurantes con autenticación multi-modal, gestión de pedidos, control de caja, inventario en tiempo real, módulo de producción y panel AdminUX unificado.

[![Django](https://img.shields.io/badge/Django-5.1.4-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![DRF](https://img.shields.io/badge/DRF-3.16-orange.svg)](https://www.django-rest-framework.org/)
[![Version](https://img.shields.io/badge/Version-40.3-blue.svg)](#)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success.svg)](#)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)

---

## 🚀 Inicio Rápido

### Opción 1: Desarrollo (SQLite)

```bash
# 1. Clonar repositorio
git clone https://github.com/KaradyGamer/Sistema-de-Gesti-n-Integral-para-Restaurantes-SGIR-.git
cd ProyectoR/restaurante_qr_project

# 2. Crear entorno virtual e instalar dependencias
python -m venv env
env\Scripts\activate  # Windows | source env/bin/activate (Linux/Mac)
pip install -r requirements.txt

# 3. Configurar variables de entorno
copy .env.example .env  # Windows | cp .env.example .env (Linux/Mac)
# Editar .env: DB_ENGINE=sqlite, SECRET_KEY segura

# 4. Inicializar base de datos
python manage.py migrate
python manage.py createsuperuser

# 5. Iniciar servidor
python manage.py runserver
```

**Acceder a**: http://127.0.0.1:8000/

### Opción 2: Producción (Docker + PostgreSQL)

```bash
# 1. Configurar variables de entorno
cp .env.example .env
# Editar .env: DB_ENGINE=postgres, credenciales PostgreSQL

# 2. Construir e iniciar contenedores
docker-compose up -d

# 3. Aplicar migraciones
docker-compose exec web python manage.py migrate

# 4. Crear superusuario
docker-compose exec web python manage.py createsuperuser
```

**Acceder a**: http://localhost:8000/

---

## ✨ Características Principales

### 🔐 Autenticación Multi-Modal
- **Password**: Administradores con autenticación Django estándar
- **PIN (4-6 dígitos)**: Cajeros con campo dedicado y validación
- **PIN Secundario**: Operaciones sensibles (eliminar pagos, anular pedidos)
- **QR (24h tokens)**: Meseros y cocineros con generación bajo demanda
- **Rate limiting**: Protección contra fuerza bruta (5 intentos, 5 min bloqueo)

### 📦 Módulo de Inventario (v40.0)
- **Insumos**: Gestión completa con categorías, unidades de medida y stock
- **DecimalField**: Soporte para cantidades fraccionarias (2.5 kg)
- **Movimientos auditados**: 6 tipos (entrada, salida, producción, ajuste, pérdida, limpieza)
- **Snapshots**: Registro de stock antes/después de cada movimiento
- **Alertas automáticas**: Stock bajo y agotado
- **Inmutabilidad**: Movimientos aplicados no se pueden modificar

### 🏭 Módulo de Producción (v40.0)
- **Recetas**: Productos fabricables con rendimiento y detalles de insumos
- **Estados de producción**: CREADO → CONFIRMADO → PREPARANDO → LISTO → ENTREGADO → APLICADO
- **Control de stock**: Insumos se descuentan SOLO al APLICAR producción
- **Trazabilidad completa**: ProduccionDetalle inmutable con snapshots
- **Tipos de producto**: Simple, Fabricable, Vendible
- **Cancelación/Anulación**: Con restauración de stock y auditoría

### 🍽️ Módulo de Pedidos (v40.2)
- **10 estados**: Creado, Confirmado, Preparando, Listo, Entregado, Solicitando Cuenta, Pagado, Cerrado, Cancelado, Anulado
- **Stock controlado**: Descuento al CONFIRMAR (no al crear)
- **Pagos parciales**: Múltiples pagos por pedido
- **Edición controlada**: Con validación de stock según estado
- **Cancelación/Anulación**: Con restauración de stock y motivo obligatorio
- **Auditoría completa**: Timestamps de todas las transiciones

### 💰 Módulo de Caja (v40.3)
- **Control de efectivo en tiempo real**: efectivo_actual actualizado automáticamente
- **Pagos parciales y mixtos**: Soporte completo con validación
- **MovimientoCaja**: 6 tipos auditados (venta, cambio, retiro, ingreso, gasto, ajuste)
- **Eliminación de pagos**: Con PIN secundario y reversión neta correcta
- **Cierre de caja (Arqueo)**: Cálculo de diferencia, validación de umbral
- **Auditoría completa**: Sin guardar PIN (solo validación booleana)

### 💼 AdminUX - Panel Unificado
- **Dashboard**: KPIs en tiempo real, gráficas de pedidos y ventas
- **Gestión completa**: Mesas, Productos, Pedidos, Reservas, Usuarios
- **Inventario**: Categorías, Insumos, Movimientos, Alertas
- **Producción**: Recetas, Órdenes de producción, Control de rendimiento
- **Caja**: Apertura/Cierre, Pagos, Movimientos, Arqueos
- **Reportes**: Análisis de ventas, productos más vendidos, inventario
- **Configuración**: Parámetros del sistema (negocio, financiero, horarios, tickets)

### 🎨 UI/UX Moderna
- **Dark Theme**: Interface oscura profesional con variables CSS
- **Sidebar vertical**: Navegación lateral con iconos Boxicons
- **Topbar responsive**: Breadcrumbs y dropdown de usuario
- **Loader animado**: Transiciones suaves entre páginas
- **Templates base**: Estructura consistente para listados y formularios
- **Charts.js**: Gráficas interactivas en dashboard

---

## 📚 Arquitectura del Sistema

### Estructura de Modelos Principales

```
USUARIOS
├─ Usuario (AbstractUser)
├─ PIN Caja (4-6 dígitos)
└─ PIN Secundario (operaciones sensibles)

INVENTARIO
├─ CategoriaInsumo
├─ Insumo (stock_actual: Decimal)
└─ MovimientoInsumo (6 tipos, inmutable)

PRODUCCIÓN
├─ Receta (producto + rendimiento)
├─ RecetaDetalle (insumo + cantidad)
├─ Produccion (estados + control stock)
└─ ProduccionDetalle (inmutable, snapshots)

PRODUCTOS
├─ Categoria
├─ Producto (tipo: simple/fabricable/vendible)
└─ Stock controlado por Producción

PEDIDOS
├─ Pedido (10 estados, stock_descontado flag)
├─ DetallePedido (stock_descontado flag)
└─ Control de stock al CONFIRMAR

CAJA
├─ Caja (efectivo_actual en tiempo real)
├─ MovimientoCaja (6 tipos, snapshots)
├─ Pago (parcial/completo, estados)
├─ DetallePago (métodos mixtos)
└─ CierreCaja (arqueo con diferencia)

MESAS Y RESERVAS
├─ Mesa (estados, capacidad, zonas)
└─ Reserva (calendario, confirmación)
```

### Flujos Principales

#### Flujo de Producción
```
1. CREAR Producción (estado='creado', stock NO descontado)
2. CONFIRMAR Producción (validar stock, crear ProduccionDetalle)
3. APLICAR Producción (descontar insumos, agregar producto fabricado)
   └─ MovimientoInsumo tipo='produccion' por cada insumo
```

#### Flujo de Pedido
```
1. CREAR Pedido (estado='creado', stock NO descontado)
2. CONFIRMAR Pedido (descontar stock de productos)
3. PREPARAR → LISTO → ENTREGAR
4. SOLICITAR CUENTA → PAGAR (parcial/completo)
5. CERRAR Pedido (liberar mesa)
```

#### Flujo de Caja
```
1. ABRIR Caja (efectivo_inicial, PIN normal)
2. REGISTRAR Pagos (simples/mixtos/parciales)
   └─ MovimientoCaja automático si hay efectivo
3. ELIMINAR Pago (PIN secundario, reversión neta)
4. CERRAR Caja (arqueo, validar diferencia)
```

---

## 🛠️ Stack Tecnológico

| Categoría | Tecnología | Versión |
|-----------|-----------|---------|
| **Backend** | Django | 5.1.4 |
| **REST API** | Django REST Framework | 3.16+ |
| **Base de Datos (Dev)** | SQLite | 3.x |
| **Base de Datos (Prod)** | PostgreSQL | 16 |
| **Python** | CPython | 3.12 |
| **Containerización** | Docker + Docker Compose | Latest |
| **Servidor WSGI** | Gunicorn | 21.2+ |
| **Proxy/Load Balancer** | Nginx | 1.25+ |
| **Frontend** | HTML5 + CSS3 + Vanilla JS | - |
| **UI Framework** | Custom CSS Variables | - |
| **Iconos** | Boxicons | 2.1.4 |
| **Gráficos** | Chart.js | 4.x |
| **Seguridad** | Django Security + JWT | - |
| **Logging** | Python logging module | - |
| **Tests** | Django TestCase + Coverage | - |

---

## 📁 Estructura del Proyecto

```
ProyectoR/
│
├── restaurante_qr_project/           ← Proyecto Django principal
│   ├── app/                          ← Apps Django
│   │   ├── adminux/                  ← Panel administrativo unificado
│   │   ├── caja/                     ← Módulo de caja (v40.3)
│   │   │   ├── models.py             ← Caja, MovimientoCaja, Pago, DetallePago, CierreCaja
│   │   │   ├── services.py           ← CajaService, PagoService
│   │   │   └── utils.py              ← Utilidades de caja
│   │   ├── cliente/                  ← Módulo de clientes (menú QR)
│   │   ├── cocinero/                 ← Panel de cocina
│   │   ├── configuracion/            ← Configuración del sistema
│   │   ├── inventario/               ← Gestión de insumos (v40.1)
│   │   │   ├── models.py             ← Insumo, MovimientoInsumo
│   │   │   └── services.py           ← MovimientoInsumoService
│   │   ├── mesero/                   ← Panel de meseros
│   │   ├── mesas/                    ← Gestión de mesas y zonas
│   │   ├── pedidos/                  ← Gestión de pedidos (v40.2)
│   │   │   ├── models.py             ← Pedido, DetallePedido
│   │   │   ├── services.py           ← PedidoService
│   │   │   └── utils.py              ← Utilidades de pedidos
│   │   ├── produccion/               ← Módulo de producción (v40.0)
│   │   │   ├── models.py             ← Receta, Produccion, ProduccionDetalle
│   │   │   └── services.py           ← ProduccionService
│   │   ├── productos/                ← Catálogo de productos
│   │   │   └── models.py             ← Producto (tipo_producto)
│   │   ├── reservas/                 ← Sistema de reservas
│   │   └── usuarios/                 ← Autenticación y usuarios
│   │       └── models.py             ← Usuario (pin_caja, pin_secundario)
│   │
│   ├── backend/                      ← Configuración Django
│   │   ├── settings.py               ← Configuración dual DB (SQLite/PostgreSQL)
│   │   ├── urls.py                   ← URLs principales
│   │   └── healthcheck.py            ← Endpoint de salud
│   │
│   ├── templates/                    ← HTML/JS/CSS
│   │   ├── css/adminux/              ← Estilos AdminUX
│   │   ├── html/adminux/             ← Templates AdminUX
│   │   │   ├── base_adminux.html     ← Layout base
│   │   │   ├── base_list.html        ← Base para listados
│   │   │   ├── base_form.html        ← Base para formularios
│   │   │   └── components/           ← Componentes reutilizables
│   │   └── js/adminux/               ← JavaScript AdminUX
│   │
│   ├── static/                       ← Archivos estáticos
│   ├── media/                        ← Archivos subidos por usuarios
│   ├── logs/                         ← Logs de aplicación
│   │
│   ├── scripts/                      ← Scripts de utilidad
│   │   └── backup.sh                 ← Script de backup
│   │
│   ├── .env.example                  ← Template de variables de entorno
│   ├── .dockerignore                 ← Archivos ignorados por Docker
│   ├── Dockerfile                    ← Imagen Docker de la aplicación
│   ├── docker-compose.yml            ← Orquestación Docker
│   ├── requirements.txt              ← Dependencias Python
│   └── manage.py                     ← CLI de Django
│
├── .gitignore                        ← Archivos ignorados por Git
└── README.md                         ← Este archivo
```

---

## 🔒 Seguridad

### Características de Seguridad Implementadas

- ✅ **Rate Limiting**: 5 intentos de login, 5 min bloqueo
- ✅ **CSRF Protection**: HttpOnly cookies, tokens CSRF
- ✅ **JWT Tokens**: Para autenticación QR con expiración 24h
- ✅ **Validación dual**: Usuario activo + permisos
- ✅ **PIN Dual**: Normal (operaciones) + Secundario (sensibles)
- ✅ **Logging seguro**: Sin PINs/passwords en logs
- ✅ **SECRET_KEY**: Desde variables de entorno
- ✅ **SQL Injection**: Protección con Django ORM
- ✅ **XSS Protection**: Escaping automático de templates
- ✅ **HTTPS Ready**: Configuración para producción
- ✅ **Auditoría completa**: Todos los cambios registrados

### Variables de Entorno Requeridas

```bash
# Django
SECRET_KEY=tu-clave-super-secreta-cambiar-en-produccion
DEBUG=False
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com

# Base de Datos
DB_ENGINE=postgres  # o 'sqlite' para desarrollo
POSTGRES_DB=sgir_db
POSTGRES_USER=sgir_user
POSTGRES_PASSWORD=tu-password-seguro
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Seguridad
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

---

## 📈 Reglas de Negocio Clave

### Inventario (52 Reglas)
- Insumos NO se descuentan en pedidos (solo en producción aplicada)
- Movimientos son inmutables después de aplicarse
- Cada movimiento registra snapshots (stock_antes, stock_despues)
- Motivo obligatorio excepto para entradas

### Producción (42 Reglas)
- Stock se descuenta SOLO al APLICAR producción (no al confirmar)
- ProduccionDetalle es inmutable (auditoría completa)
- Estados APLICADA y CANCELADA son irreversibles
- Receta pertenece a UN producto fabricable con rendimiento

### Pedidos (57 Reglas)
- Stock de productos se descuenta al CONFIRMAR (no al crear)
- Campo stock_descontado previene doble descuento
- Productos agotados NO se pueden agregar a pedidos
- Cancelación restaura stock, anulación requiere Admin

### Caja (29 Reglas)
- Solo UNA caja abierta por cajero a la vez
- efectivo_actual se actualiza automáticamente con MovimientoCaja
- Pagos eliminados requieren PIN secundario (NO se borran de BD)
- Diferencia en cierre requiere observaciones si > umbral

---

## 🧪 Testing

```bash
# Ejecutar todos los tests
python manage.py test

# Tests específicos por módulo
python manage.py test app.usuarios.tests
python manage.py test app.inventario.tests
python manage.py test app.produccion.tests
python manage.py test app.pedidos.tests
python manage.py test app.caja.tests

# Con cobertura
coverage run --source='.' manage.py test
coverage report
coverage html  # Genera reporte HTML en htmlcov/
```

---

## 🐳 Docker

### Desarrollo

```bash
# Iniciar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f web

# Ejecutar comandos
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser

# Detener servicios
docker-compose down
```

### Producción

```bash
# Build con tag de versión
docker build -t sgir:40.3 .

# Deploy con variables de entorno
docker-compose -f docker-compose.prod.yml up -d

# Backup de base de datos
docker-compose exec db pg_dump -U sgir_user sgir_db > backup_$(date +%Y%m%d).sql
```

---

## 📊 Changelog v40.3

### ✨ Módulo de Caja Completo
- **Caja**: Control de efectivo en tiempo real
- **MovimientoCaja**: 6 tipos con snapshots (venta, cambio, retiro, ingreso, gasto, ajuste)
- **Pago**: Soporte para parciales, mixtos, eliminación auditada
- **DetallePago**: Desglose de métodos para pagos mixtos
- **CierreCaja**: Arqueo con validación de diferencia

### 🔧 Correcciones Técnicas v40.3.1
- **MovimientoCaja.save()**: Bloqueo basado en estado anterior en BD
- **calcular_efectivo_esperado()**: Suma directa sin doble descuento
- **Eliminación de pago**: Reversión neta correcta (incluye cambio)
- **Auditoría de PIN**: pin_secundario_validado (booleano, no PIN real)

### 📦 v40.0 - v40.2
- **Inventario**: Insumos con Decimal, 6 tipos de movimientos, inmutabilidad
- **Producción**: Recetas, estados, ProduccionDetalle, trazabilidad completa
- **Pedidos**: 10 estados, stock controlado, pagos parciales, cancelación/anulación

### 🎨 v39.5
- **AdminUX**: Panel unificado con diseño dark theme
- **Configuración**: Parámetros centralizados del sistema
- **PIN para usuarios**: Campo dedicado para cajeros
- **Generación de QR**: API bajo demanda para meseros/cocineros

---

## 🐛 Soporte y Contribución

### Reportar Problemas
- [Issues en GitHub](https://github.com/KaradyGamer/Sistema-de-Gesti-n-Integral-para-Restaurantes-SGIR-/issues)

### Documentación Adicional
- **Guía de Desarrollo**: Ver `/docs/development.md`
- **Guía de Deploy**: Ver `/docs/deployment.md`
- **API Documentation**: Ver `/docs/api.md`

---

## 📄 Licencia

Este proyecto es privado y confidencial. Todos los derechos reservados.

---

## 🏆 Estado del Proyecto

| Aspecto | Estado |
|---------|--------|
| **Versión** | 40.3.1 |
| **Última actualización** | 2025-01-22 |
| **Estado** | ✅ Production Ready |
| **Cobertura de Tests** | En desarrollo |
| **Módulos Completados** | 7/7 (Usuarios, Inventario, Producción, Productos, Pedidos, Caja, AdminUX) |
| **Documentación** | Completa |
| **Docker** | ✅ Listo |
| **PostgreSQL** | ✅ Soportado |

### Próximas Fases
- 🔄 Implementación de Services completos
- 🧪 Aumento de cobertura de tests (objetivo: 80%+)
- 📱 API REST completa con serializers
- 🔐 Sistema de permisos granular por rol
- 📊 Reportes avanzados y analytics
- 🌐 Internacionalización (i18n)

---

**Desarrollado con** ❤️ **usando Django + Python + Docker**

**Arquitectura diseñada para**: Escalabilidad, Auditoría Completa, Seguridad Enterprise

