# 🍽️ SGIR - Sistema de Gestión Integral para Restaurantes

**Versión:** 2.3.0
**Framework:** Django 5.1.4
**Python:** 3.12
**Base de Datos:** PostgreSQL (Producción) / SQLite (Desarrollo)

---

## 📋 Descripción del Sistema

**SGIR** es un sistema completo de gestión para restaurantes medianos y grandes, diseñado con arquitectura desacoplada que permite flexibilidad total en el frontend mientras mantiene un backend robusto y estable.

### ¿Qué Problemas Resuelve?

- ✅ Gestión completa del flujo de pedidos (desde QR hasta pago)
- ✅ Control de caja con cierres de turno y jornada laboral
- ✅ Sistema de reservas con validación de disponibilidad
- ✅ Inventario con alertas de stock bajo
- ✅ Reportes de ventas (PDF y Excel)
- ✅ Autenticación múltiple (password, PIN, QR)
- ✅ Auditoría completa de todas las operaciones
- ✅ Multi-dispositivo (tablets, móviles, desktop)

### Arquitectura General

```
┌─────────────────────────────────────────────────────┐
│                   FRONTEND (A DEFINIR)               │
│   Web / SPA / App Móvil / Tablets / 3D / Kiosko    │
└──────────────────┬──────────────────────────────────┘
                   │
                   │ REST API (JWT + Session)
                   │
┌──────────────────▼──────────────────────────────────┐
│              BACKEND DJANGO (FROZEN)                 │
│  ✓ API REST completa con DRF                        │
│  ✓ Máquina de estados estricta                      │
│  ✓ Validaciones de negocio                          │
│  ✓ Autenticación multi-método                       │
│  ✓ Auditoría y logging                              │
│  ✓ Soft delete                                      │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│            PostgreSQL 16 / SQLite                    │
└─────────────────────────────────────────────────────┘
```

---

## 🎯 Funcionalidades Actuales

### 1. Gestión de Pedidos (Máquina de Estados)

**Flujo completo del pedido:**

```
creado → confirmado → en_preparación → listo → entregado → cerrado
```

- Control estricto de transiciones de estado
- Validación de stock en tiempo real
- Sistema de modificación con auditoría
- Cancelación con devolución de stock
- Pagos parciales y totales
- Reembolsos con autorización

### 2. Sistema de Caja

- Procesamiento de pagos múltiples: efectivo, tarjeta, QR, móvil, mixto
- Cierres de turno: mañana, tarde, noche, completo
- Control de diferencias: efectivo esperado vs real
- Validación: no permite cerrar con pedidos pendientes
- Jornada laboral única activa
- Historial completo de transacciones

### 3. Reservas

- Validación de disponibilidad automática
- Detección de solapamiento de horarios
- Sistema de No-Show (liberación automática tras 15 min)
- Estados: pendiente, confirmada, en_uso, completada, cancelada, no_show
- Notificaciones y recordatorios
- Política de cancelación (2 horas de anticipación)

### 4. Reportes y Estadísticas

- Generación de reportes en **PDF** y **XLSX**
- Tipos: diario, semanal, mensual, personalizado
- Análisis por producto
- Métricas: ventas totales, promedio por pedido, productos más vendidos
- Dashboard con estadísticas en tiempo real
- Gráficos de tendencias

### 5. Usuarios y Roles

**Roles disponibles:**
- `admin` - Acceso total
- `gerente` - Gestión y reportes
- `cajero` - Caja y transacciones (login con PIN)
- `mesero` - Gestión de mesas y pedidos (login con QR)
- `cocinero` - Panel de cocina (login con QR)
- `cliente` - Vista del menú QR

**Características de seguridad:**
- Rate limiting (5 intentos, bloqueo 5 min)
- Tokens QR expirables (24 horas)
- Soft delete (no eliminación física)
- Auditoría de cambios
- Permisos multi-área

### 6. Sistema QR

**Mesas:**
- QR único por mesa
- Redirección automática al menú
- Estado de mesa en tiempo real

**Empleados:**
- QR de autenticación one-time use
- Tokens renovables
- Expiración automática

### 7. Inventario

- Control de insumos y materias primas
- Alertas automáticas de stock bajo/agotado
- Movimientos: entrada, salida, ajuste
- Historial completo con auditoría
- Múltiples unidades de medida

---

## 📊 Estado Actual del Proyecto

### ✅ Backend: CERRADO / FROZEN

El backend está **completamente terminado, auditado y congelado**:

- ✓ 10 apps Django bien estructuradas
- ✓ ~161 archivos Python
- ✓ API REST completa con Django REST Framework
- ✓ Autenticación JWT + Session + QR + PIN
- ✓ Validaciones de negocio estrictas
- ✓ Tests de seguridad implementados
- ✓ Logging y auditoría completos
- ✓ Docker listo para producción
- ✓ Migraciones aplicadas
- ✓ Sin deuda técnica crítica

⚠️ **IMPORTANTE:** El backend **NO debe modificarse**. Toda la lógica de negocio está validada y lista para producción.

### 🚧 Frontend: ELIMINADO / A RECONSTRUIR

El frontend anterior ha sido **completamente eliminado** para permitir:

- 🎨 Diseño UI/UX desde cero
- 🚀 Libertad total de tecnología (React, Vue, Angular, etc.)
- 📱 Diseño responsive moderno
- 🎯 Enfoque en experiencia de usuario
- 🌐 PWA, SPA o arquitectura tradicional

**Posibilidades de frontend:**
1. **Web tradicional** - Server-side rendering con Django templates
2. **SPA (React/Vue/Angular)** - Consumo de API REST
3. **App móvil nativa** - React Native, Flutter
4. **Tablets para meseros** - Interfaz optimizada
5. **Menú 3D interactivo** - Three.js, WebGL
6. **Pantallas de cocina** - Display en tiempo real
7. **Dashboard de caja** - Métricas y gráficos
8. **Kiosko de autoservicio** - Pedidos directos

### 💾 Base de Datos: Lista para Producción

- Schema completamente definido
- Migraciones aplicadas y validadas
- Índices optimizados
- Relaciones intactas
- Datos de prueba disponibles

### 🐳 Docker: Listo

- `Dockerfile` optimizado
- `docker-compose.yml` para desarrollo
- `docker-compose.prod.yml` para producción
- Health checks configurados
- Volúmenes persistentes

---

## 🚀 Cómo Levantar el Proyecto (DEV)

### 1. Clonar el Repositorio

```bash
git clone <repo-url>
cd restaurante_qr_project
```

### 2. Configurar Variables de Entorno

Copiar `.env.example` a `.env` y configurar:

```env
# Django
SECRET_KEY=tu-secret-key-super-secreta
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de Datos
DB_ENGINE=sqlite  # o 'postgres' para producción
POSTGRES_DB=sgir_db
POSTGRES_USER=sgir_user
POSTGRES_PASSWORD=password_seguro
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Configuración adicional
LANGUAGE_CODE=es-bo
TIME_ZONE=America/La_Paz
```

### 3. Levantar con Docker (Recomendado)

```bash
# Desarrollo
docker-compose up -d

# Producción
docker-compose -f docker-compose.prod.yml up -d
```

### 4. O Levantar Manual (Sin Docker)

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Cargar datos de prueba (opcional)
python scripts/crear_datos_iniciales.py

# Levantar servidor
python manage.py runserver
```

### 5. Acceder al Sistema

- **Django Admin:** http://localhost:8000/admin/
- **API REST:** http://localhost:8000/api/
- **Health Check:** http://localhost:8000/health/

---

## 📚 Comandos Principales

```bash
# Migraciones
python manage.py makemigrations
python manage.py migrate

# Crear datos iniciales
python scripts/crear_datos_iniciales.py

# Regenerar QR de mesas
python scripts/regenerar_qr.py

# Regenerar QR de empleados
python scripts/regenerar_qr_empleados.py

# Tests
pytest
python manage.py test

# Linting
ruff check .

# Colectar estáticos
python manage.py collectstatic --noinput

# Backup de SQLite
python scripts/backup_sqlite.py
```

---

## 📂 Estructura del Proyecto

```
restaurante_qr_project/
├── backend/                    # Configuración Django
│   ├── settings.py            # Configuración principal
│   ├── urls.py                # Rutas principales
│   └── healthcheck.py         # Endpoint de monitoreo
│
├── app/                        # Apps Django (módulos)
│   ├── adminux/               # Panel de administración moderno
│   ├── caja/                  # Caja y transacciones
│   ├── configuracion/         # Configuración del sistema
│   ├── inventario/            # Gestión de insumos
│   ├── mesas/                 # Gestión de mesas y QR
│   ├── pedidos/               # Comandas y pedidos
│   ├── productos/             # Productos y categorías
│   ├── reportes/              # Reportes y estadísticas
│   ├── reservas/              # Sistema de reservas
│   └── usuarios/              # Autenticación y usuarios
│
├── scripts/                    # Scripts de utilidad
│   ├── crear_datos_iniciales.py
│   ├── regenerar_qr.py
│   ├── regenerar_qr_empleados.py
│   ├── actualizar_mesas.py
│   └── backup_sqlite.py
│
├── media/                      # Archivos subidos (QR, imágenes)
├── logs/                       # Logs del sistema
├── requirements.txt            # Dependencias Python
├── Dockerfile                  # Imagen Docker
├── docker-compose.yml          # Orquestación
├── .env.example               # Ejemplo de variables
├── ruff.toml                  # Configuración linter
└── VERSION                    # Versión del sistema
```

---

## 🔌 API REST

### Endpoints Principales

**Autenticación:**
- `POST /api/token/` - Obtener JWT token
- `POST /api/token/refresh/` - Refresh token
- `POST /usuarios/session-login/` - Login con sesión
- `POST /usuarios/login-pin/` - Login con PIN (cajeros)
- `GET /qr-login/<uuid>/` - Login con QR (meseros/cocineros)

**Productos:**
- `GET /api/productos/` - Listar productos
- `GET /api/productos/categorias/` - Listar categorías
- `POST /api/productos/` - Crear producto
- `PUT /api/productos/{id}/` - Actualizar producto
- `DELETE /api/productos/{id}/` - Eliminar producto (soft delete)

**Mesas:**
- `GET /api/mesas/` - Listar mesas
- `POST /api/mesas/` - Crear mesa
- `PATCH /api/mesas/{id}/` - Actualizar estado

**Pedidos:**
- `GET /api/pedidos/` - Listar pedidos
- `GET /api/pedidos/cocina/` - Pedidos en cocina
- `GET /api/pedidos/mesero/` - Pedidos por mesa
- `POST /api/pedidos/{id}/actualizar/` - Actualizar estado
- `POST /api/pedidos/{id}/entregar/` - Marcar entregado
- `POST /api/pedidos/{id}/cancelar/` - Cancelar pedido

**Caja:**
- `GET /api/caja/transacciones/` - Listar transacciones
- `POST /api/caja/procesar-pago/` - Procesar pago
- `GET /api/caja/cierres/` - Cierres de caja
- `POST /api/caja/cierre/` - Crear cierre

**Reservas:**
- `GET /api/reservas/` - Listar reservas
- `POST /api/reservas/` - Crear reserva
- `PATCH /api/reservas/{id}/` - Actualizar reserva
- `DELETE /api/reservas/{id}/` - Cancelar reserva

**Reportes:**
- `GET /api/reportes/` - Listar reportes
- `POST /api/reportes/generar/` - Generar reporte
- `GET /api/reportes/{id}/excel/` - Descargar Excel
- `GET /api/reportes/{id}/pdf/` - Descargar PDF

Toda la API está documentada y requiere autenticación JWT o Session.

---

## 🔐 Seguridad

### Implementaciones de Seguridad

- ✅ **CSRF Protection** - Tokens CSRF en todos los formularios
- ✅ **Rate Limiting** - 5 intentos de login, bloqueo de 5 minutos
- ✅ **JWT Tokens** - Access (1h) + Refresh (14 días) con rotación
- ✅ **Cookies Seguras** - HttpOnly, Secure (HTTPS), SameSite=Lax
- ✅ **CORS Configurado** - Orígenes permitidos controlados
- ✅ **Soft Delete** - No eliminación física de registros críticos
- ✅ **Auditoría** - HistorialModificación en todas las operaciones
- ✅ **Validaciones Estrictas** - Máquina de estados con constantes
- ✅ **Logging Completo** - Rotación diaria, logs de errores separados
- ✅ **HTTPS Enforced** - Redirección SSL en producción
- ✅ **HSTS** - Strict-Transport-Security configurado

### Variables de Entorno Críticas

```env
SECRET_KEY=<CAMBIAR-EN-PRODUCCION>
DEBUG=False  # En producción
ALLOWED_HOSTS=tudominio.com,www.tudominio.com
```

---

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest

# Tests con coverage
pytest --cov=app --cov-report=html

# Tests específicos
pytest app/pedidos/tests/
pytest app/caja/tests/

# Tests de seguridad
pytest app/pedidos/tests/test_seguridad_ronda1.py
```

**Cobertura actual:**
- Tests de flujo de pedidos
- Tests de seguridad (Rondas 1-3)
- Tests de jornada laboral
- Tests de autenticación
- Tests de reservas

---

## 📦 Dependencias Principales

```
Django==5.1.4                      # Framework principal
djangorestframework==3.15.2        # API REST
djangorestframework-simplejwt==5.3.1  # Autenticación JWT
django-cors-headers==4.6.0         # CORS
whitenoise==6.8.2                  # Archivos estáticos
gunicorn==23.0.0                   # Servidor WSGI
python-decouple==3.8               # Variables de entorno
psycopg2-binary==2.9.10           # PostgreSQL
qrcode==8.0                        # Códigos QR
Pillow==11.0.0                     # Procesamiento de imágenes
openpyxl==3.1.5                    # Generación de Excel
reportlab==4.2.5                   # Generación de PDF
pytest==8.3.4                      # Testing
```

---

## 🌍 Localización

**Configurado para Bolivia:**
- Idioma: Español (es-bo)
- Zona horaria: America/La_Paz
- Moneda: Bs/ (Boliviano)
- Formato numérico: separador de miles (.), decimal (,)

---

## 📈 Roadmap de Frontend

### Fase 1: Definición
- [ ] Diseño UI/UX completo
- [ ] Selección de tecnología frontend
- [ ] Arquitectura de componentes
- [ ] Sistema de diseño (Design System)

### Fase 2: Core
- [ ] Autenticación y login
- [ ] Dashboard principal
- [ ] Panel de empleados

### Fase 3: Operaciones
- [ ] Panel de cocina (tiempo real)
- [ ] Panel de mesero (mesas y pedidos)
- [ ] Panel de caja (pagos y cierres)

### Fase 4: Gestión
- [ ] Panel AdminUX (CRUD completo)
- [ ] Reportes visuales
- [ ] Configuración del sistema

### Fase 5: Extras
- [ ] PWA (instalable)
- [ ] Notificaciones push
- [ ] Modo offline
- [ ] Menú 3D interactivo

---

## ⚠️ Nota Importante

> ### 🚨 EL FRONTEND SERÁ RECONSTRUIDO DESDE CERO
>
> El frontend anterior ha sido eliminado intencionalmente para permitir:
> - Diseño moderno y centrado en el usuario
> - Libertad total en la elección de tecnología
> - Optimización para múltiples dispositivos
> - Experiencia de usuario excepcional
>
> **NO USAR CÓDIGO FRONTEND PREVIO.**
>
> El backend está **FROZEN** y no debe modificarse. Toda la lógica de negocio
> está completa, validada y lista para producción.

---

## 📞 Soporte y Contribución

### Reportar Issues

Si encuentras un bug o tienes una sugerencia:

1. Verifica que sea un problema del **backend** (API/lógica)
2. Revisa si ya existe un issue similar
3. Crea un issue con descripción detallada
4. Incluye logs si es posible

### Reglas de Contribución

- ❌ **NO modificar lógica del backend** (está frozen)
- ✅ Documentación adicional es bienvenida
- ✅ Mejoras en comentarios del código
- ✅ Sugerencias de optimización (sin implementar)
- ✅ Reporte de bugs con reproducción

---

## 📄 Licencia

Este proyecto es **propiedad privada**. Todos los derechos reservados.

No se permite:
- Uso comercial sin autorización
- Redistribución del código
- Modificación sin permiso explícito

---

## 🎓 Créditos

**SGIR v2.3.0**
Sistema de Gestión Integral para Restaurantes
Desarrollado con Django 5.1.4 y Python 3.12

---

## 📌 Links Útiles

- [Documentación de Django](https://docs.djangoproject.com/en/5.1/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)

---

**Última actualización:** 2026-01-07
**Versión del README:** 1.0.0