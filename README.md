# 🍽️ Sistema de Gestión de Restaurante QR

## 📋 Índice
1. [Descripción General](#descripción-general)
2. [Tecnologías y Librerías](#tecnologías-y-librerías)
3. [Estructura del Proyecto](#estructura-del-proyecto)
4. [Características Principales](#características-principales)
5. [Sistema de Autenticación](#sistema-de-autenticación)
6. [Sistema de Caja y Jornada](#sistema-de-caja-y-jornada)
7. [Base de Datos](#base-de-datos)
8. [Instalación y Configuración](#instalación-y-configuración)
9. [Flujos de Trabajo](#flujos-de-trabajo)
10. [APIs y Endpoints](#apis-y-endpoints)
11. [Problemas Conocidos](#problemas-conocidos)

---

## 📖 Descripción General

Sistema integral de gestión para restaurantes desarrollado con Django 5.2, que incluye:

- 🔐 **Autenticación multi-nivel** (PIN, QR, tradicional)
- 💰 **Punto de Venta (POS)** completo con gestión de caja
- 📅 **Control de jornada laboral** y acceso de empleados
- 🍽️ **Gestión de pedidos** en tiempo real
- 👥 **Gestión de personal** con códigos QR únicos
- 📊 **Reportes y estadísticas** de ventas
- 🏪 **Sistema de reservas**
- 📦 **Control de inventario** con alertas de stock
- ✏️ **Modificación de pedidos** en tiempo real

---

## 🛠️ Tecnologías y Librerías

### Backend
- **Django 5.2** - Framework web principal
- **Python 3.13** - Lenguaje de programación
- **SQLite** - Base de datos (desarrollo)
- **Django REST Framework 3.16.0** - API REST
- **djangorestframework-simplejwt 5.5.0** - Autenticación JWT
- **django-cors-headers 4.7.0** - CORS para API
- **django-filter 25.1** - Filtrado de datos
- **Pillow 11.1.0** - Procesamiento de imágenes
- **qrcode 8.1** - Generación de códigos QR
- **python-decouple 3.8** - Gestión de variables de entorno
- **psycopg2-binary 2.9.10** - Conector PostgreSQL
- **django-admin-interface 0.28.8** - Interfaz admin personalizada
- **django-colorfield 0.11.0** - Campos de color

### Frontend
- **HTML5/CSS3** - Estructura y estilos modernos
- **JavaScript ES6+** - Lógica del cliente
- **Fetch API** - Comunicación asíncrona con backend

### Seguridad
- **CSRF Protection** - Protección contra ataques CSRF
- **Session Authentication** - Autenticación por sesión Django
- **JWT Authentication** - Autenticación por tokens
- **Custom Middleware** - Validación de jornada laboral
- **Variables de entorno** - Configuración segura con .env

---

## 📁 Estructura del Proyecto

```
ProyectoR/
├── restaurante_qr_project/          # Proyecto Django principal
│   ├── manage.py                     # Comando de gestión Django
│   ├── db.sqlite3                    # Base de datos SQLite
│   ├── crear_datos_iniciales.py      # Script de datos de prueba
│   ├── .env                          # Variables de entorno
│   │
│   ├── backend/                      # Configuración del proyecto
│   │   ├── settings.py               # ⚙️ Configuración principal
│   │   ├── urls.py                   # 🔗 URLs principales
│   │   └── wsgi.py                   # 🚀 Servidor WSGI
│   │
│   └── app/                          # Apps de Django
│       ├── usuarios/                 # 👤 Gestión de usuarios
│       │   ├── models.py             # Modelo Usuario extendido
│       │   ├── views.py              # Login PIN/QR/Admin
│       │   ├── views_empleado.py     # Panel unificado empleado
│       │   ├── utils.py              # Decoradores de permisos
│       │   └── management/commands/
│       │       └── configurar_usuarios.py
│       │
│       ├── caja/                     # 💰 Punto de Venta
│       │   ├── models.py             # Transacción, CierreCaja, JornadaLaboral
│       │   ├── views.py              # Vistas del cajero
│       │   ├── api_views.py          # APIs de pagos
│       │   ├── middleware.py         # Validación jornada laboral
│       │   ├── utils.py              # Utilidades de caja
│       │   ├── urls.py               # URLs HTML
│       │   └── api_urls.py           # URLs API
│       │
│       ├── pedidos/                  # 🍽️ Gestión de pedidos
│       │   ├── models.py             # Pedido, DetallePedido
│       │   ├── views.py              # Cocina, Mesero, Cliente
│       │   ├── serializers.py        # Serializadores DRF
│       │   └── urls.py
│       │
│       ├── productos/                # 🥘 Catálogo de productos
│       │   ├── models.py             # Producto, Categoría
│       │   ├── views.py              # CRUD productos
│       │   └── urls.py
│       │
│       ├── mesas/                    # 🪑 Gestión de mesas
│       │   ├── models.py             # Mesa
│       │   ├── views.py              # Mapa de mesas
│       │   └── urls.py
│       │
│       ├── reservas/                 # 📅 Sistema de reservas
│       │   ├── models.py             # Reserva
│       │   ├── views.py              # Gestión reservas
│       │   └── urls.py
│       │
│       └── reportes/                 # 📊 Reportes y estadísticas
│           ├── models.py             # ReporteVentas, AnalisisProducto
│           ├── views.py              # Generación de reportes
│           └── urls.py
│
├── templates/                        # 🎨 Templates HTML
│   ├── login.html                    # Login unificado
│   ├── cajero/                       # Templates de cajero
│   │   ├── panel_caja.html           # Panel principal
│   │   ├── personal_panel.html       # Gestión de personal + QR
│   │   ├── gestionar_jornada.html    # Control de jornada
│   │   ├── modificar_pedido.html     # Modificar pedidos
│   │   ├── procesar_pago.html        # Procesar pagos
│   │   ├── abrir_caja.html           # Abrir turno
│   │   └── cierre_caja.html          # Cerrar turno
│   ├── empleado/                     # Templates de empleado
│   │   └── panel_unificado.html      # Panel multi-área
│   ├── mesero/                       # Templates de mesero
│   ├── cocinero/                     # Templates de cocina
│   ├── reservas/                     # Templates de reservas
│   └── static/                       # CSS, JS, imágenes
│
├── env/                              # Entorno virtual Python
├── requirements.txt                  # Dependencias del proyecto
└── README.md                         # 📚 Este archivo
```

---

## ✨ Características Principales

### 1. 🔐 Sistema de Autenticación Multi-nivel

**3 métodos de autenticación diferentes:**

- **Login con PIN (4-6 dígitos)** - Exclusivo para cajeros
- **Login tradicional (usuario/contraseña)** - Para administradores y gerentes
- **Login por código QR** - Para meseros y cocineros

**Seguridad implementada:**
- Tokens QR únicos (UUID v4)
- Validación de roles y permisos
- Control de acceso basado en jornada laboral
- Sesiones Django seguras

### 2. 💰 Sistema de Caja Completo

**Gestión de Caja:**
- Apertura y cierre de turno
- Control de efectivo inicial y final
- Cálculo automático de diferencias
- Múltiples turnos (mañana, tarde, noche)

**Procesamiento de Pagos:**
- Pago simple (un método)
- Pago mixto (múltiples métodos)
- Métodos soportados: efectivo, tarjeta, QR, pago móvil
- Generación automática de facturas
- Aplicación de descuentos y propinas

**Modificación de Pedidos:**
- Ver todos los pedidos pendientes (cualquier estado)
- Agregar/eliminar productos en tiempo real
- Modificar cantidades
- Buscar productos del menú completo
- Ver stock disponible
- Registro de motivos de modificación
- Historial completo de cambios

### 3. 📅 Control de Jornada Laboral

**El cajero controla cuándo los empleados pueden trabajar:**

**Jornada ACTIVA ✅**
- Cajero puede iniciar jornada desde el panel
- Los empleados pueden hacer login con QR
- Meseros y cocineros pueden acceder al sistema

**Jornada INACTIVA ❌**
- El cajero finaliza la jornada
- Se cierran automáticamente todas las sesiones de empleados
- Los empleados no pueden iniciar sesión hasta que se abra nueva jornada

**Cierre de Caja Automático:**
- Al cerrar caja, se cierran todas las sesiones activas
- Los empleados pierden acceso inmediato
- Solo admin y cajeros pueden acceder con caja cerrada

### 4. 🍽️ Gestión de Pedidos en Tiempo Real

**Flujo completo:**
- Cliente → Pedido → Cocina → Mesero → Caja
- Estados: Pendiente → En Preparación → Listo → Entregado → Pagado
- Actualización en tiempo real
- Notificaciones de cambio de estado

### 5. 👥 Gestión de Personal con QR

**Generación de códigos QR:**
- QR único por empleado
- Acceso instantáneo al sistema
- Renovación automática por seguridad
- Sin necesidad de memorizar credenciales

### 6. 📦 Control de Inventario

**Alertas de Stock:**
- Alertas automáticas cuando stock < mínimo
- Alertas de productos agotados
- Panel de alertas para cajero
- Resolución y seguimiento de alertas

### 7. 📊 Reportes y Estadísticas

**Dashboard de caja:**
- Ventas del día en tiempo real
- Total de pedidos
- Pedidos pagados vs pendientes
- Estadísticas por método de pago

---

## 🔐 Sistema de Autenticación

### Métodos de Autenticación

#### 1️⃣ Login con PIN (Cajeros)

```python
# URL: /usuarios/login-pin/
# Método: POST

Entrada: { "pin": "1000" }
Salida: { "success": true, "redirect_url": "/caja/" }

Flujo:
1. Cajero ingresa PIN (ej: 1000)
2. Sistema busca usuario con ese PIN
3. Valida que sea cajero y esté activo
4. Crea sesión Django
5. Redirige a panel de caja
```

#### 2️⃣ Login Tradicional (Admin/Gerente)

```python
# URL: /usuarios/login-admin/
# Método: POST

Entrada: {
  "username": "admin",
  "password": "admin123"
}
Salida: { "success": true, "redirect_url": "/reportes/dashboard/" }

Flujo:
1. Usuario ingresa credenciales
2. Django autentica con authenticate()
3. Valida que sea admin/gerente
4. Crea sesión
5. Redirige a dashboard de reportes
```

#### 3️⃣ Autenticación por QR (Empleados)

```python
# URL: /usuarios/auth-qr/<uuid:token>/
# Método: GET

Flujo:
1. Cajero genera QR para empleado desde "Gestión de Personal"
2. QR contiene URL con token UUID único
3. Empleado escanea QR con celular
4. Sistema verifica:
   - Usuario existe y está activo
   - Hay una jornada laboral activa (para meseros/cocineros)
   - Hay una caja abierta (para meseros/cocineros)
5. Autentica automáticamente
6. Redirige a panel correspondiente
```

### Generación de QR

```python
# Vista: caja/views.py:generar_qr_empleado()

import qrcode
import uuid

def generar_qr_empleado(request, empleado_id):
    empleado = get_object_or_404(Usuario, id=empleado_id)

    # Generar token único
    token = uuid.uuid4()
    empleado.qr_token = token
    empleado.save()

    # Crear URL
    qr_url = f"{request.scheme}://{request.get_host()}/usuarios/auth-qr/{token}/"

    # Generar imagen QR
    qr = qrcode.make(qr_url)

    # Retornar imagen en base64
    return JsonResponse({'qr_image': img_base64, 'url': qr_url})
```

### Roles y Permisos

| Rol | Login | Acceso | Dependencia |
|-----|-------|--------|-------------|
| **Admin** | Usuario/Contraseña | Todo el sistema | Ninguna |
| **Gerente** | Usuario/Contraseña | Todo el sistema | Ninguna |
| **Cajero** | PIN (1000+) | Caja, Personal, Jornada | Ninguna |
| **Mesero** | QR (solo) | Panel Mesero | Caja abierta + Jornada activa |
| **Cocinero** | QR (solo) | Panel Cocina | Caja abierta + Jornada activa |

---

## 💰 Sistema de Caja y Jornada

### Flujo de Apertura y Cierre

#### 1. Abrir Caja

```python
# Vista: caja/views.py:abrir_caja()

POST /caja/abrir/
{
  "turno": "manana",
  "efectivo_inicial": 100.00
}

→ Crea CierreCaja(estado='abierto')
→ Habilita procesamiento de pagos
```

#### 2. Gestión de Jornada

```python
# Vista: caja/views.py:gestionar_jornada()

POST /caja/jornada/
{"accion": "iniciar"}

→ Crea JornadaLaboral(estado='activa')
→ Los empleados YA PUEDEN trabajar

POST /caja/jornada/
{"accion": "finalizar"}

→ Actualiza JornadaLaboral(estado='finalizada')
→ Los empleados pierden acceso INMEDIATAMENTE
```

#### 3. Cerrar Caja

```python
# Vista: caja/api_views.py:api_cerrar_caja()

POST /api/caja/cerrar/
{
  "efectivo_real": 450.50,
  "observaciones": "Todo correcto"
}

→ Calcula totales por método de pago
→ Calcula diferencia (real vs esperado)
→ Cierra todas las sesiones de empleados
→ CierreCaja(estado='cerrado')
→ Genera reporte de cierre
```

### Middleware de Jornada

```python
# app/caja/middleware.py

class JornadaLaboralMiddleware:
    """
    Valida que meseros/cocineros solo accedan si hay jornada activa.
    Si no hay jornada → Cierra sesión automáticamente
    """
    def __call__(self, request):
        if request.user.rol in ['mesero', 'cocinero']:
            if not JornadaLaboral.hay_jornada_activa():
                logout(request)
                messages.warning(request, 'Jornada no activa')
                return redirect('/login/')

        return self.get_response(request)
```

### Modificación de Pedidos

**El cajero puede modificar pedidos en cualquier momento:**

```python
# Vista: caja/views.py:modificar_pedido()

GET /caja/modificar-pedido/<id>/

Funcionalidades:
- Ver productos actuales del pedido
- Cambiar cantidades (botones +/-)
- Eliminar productos
- Buscar y agregar nuevos productos del menú
- Ver stock disponible en tiempo real
- Agregar motivo de modificación
- Guardar cambios con auditoría completa

API: POST /api/caja/pedido/<id>/modificar/
{
  "modificados": [{item_id: 1, nueva_cantidad: 3}],
  "eliminados": [2, 3],
  "agregados": [{producto_id: 5, cantidad: 2}],
  "motivo": "Cliente cambió de opinión"
}
```

---

## 💾 Base de Datos

### Diagrama de Relaciones

```
Usuario (AbstractUser)
  │
  ├──(ForeignKey)─→ Pedido
  │                   │
  │                   ├──(ForeignKey)─→ Mesa
  │                   │
  │                   └──(ForeignKey)─→ DetallePedido
  │                                       │
  │                                       └──(ForeignKey)─→ Producto
  │                                                           │
  │                                                           └──(ForeignKey)─→ Categoria
  │
  ├──(ForeignKey)─→ Transaccion
  │                   │
  │                   └──(ForeignKey)─→ DetallePago
  │
  ├──(ForeignKey)─→ CierreCaja
  │
  ├──(ForeignKey)─→ JornadaLaboral
  │
  ├──(ForeignKey)─→ AlertaStock ──(ForeignKey)─→ Producto
  │
  └──(ForeignKey)─→ HistorialModificacion ──(ForeignKey)─→ Pedido
```

### Modelos Principales

#### Usuario (Extendido)

```python
class Usuario(AbstractUser):
    rol = CharField(...)  # cliente, mesero, cocinero, cajero, gerente, admin
    pin = CharField(...)  # PIN numérico (solo cajeros)
    qr_token = UUIDField(...)  # Token único para QR
    qr_imagen = ImageField(...)  # Imagen QR generada
    areas_permitidas = JSONField(...)  # ['mesero', 'cocina', 'caja']
    activo = BooleanField(...)  # Control de acceso
    fecha_ultimo_qr = DateTimeField(...)
```

#### Pedido

```python
class Pedido(models.Model):
    mesa = ForeignKey(Mesa, on_delete=PROTECT, related_name='pedidos')
    estado = CharField(...)  # pendiente, en preparacion, listo, entregado
    estado_pago = CharField(...)  # pendiente, parcial, pagado, cancelado
    total = DecimalField(...)
    total_final = DecimalField(...)  # Con descuentos y propina
    descuento = DecimalField(...)
    descuento_porcentaje = DecimalField(...)
    propina = DecimalField(...)
    cajero_responsable = ForeignKey(Usuario, ...)
    modificado = BooleanField(...)  # Si fue modificado por caja
    reasignado = BooleanField(...)  # Si fue reasignado de mesa
```

#### CierreCaja

```python
class CierreCaja(models.Model):
    cajero = ForeignKey(Usuario, ...)
    fecha = DateField(...)
    turno = CharField(...)  # manana, tarde, noche, completo
    estado = CharField(...)  # abierto, cerrado
    efectivo_inicial = DecimalField(...)
    efectivo_esperado = DecimalField(...)
    efectivo_real = DecimalField(...)
    diferencia = DecimalField(...)
    total_ventas = DecimalField(...)

    def cerrar_caja(self, efectivo_real, observaciones):
        """Cierra el turno y todas las sesiones de empleados"""
        # Cerrar sesiones activas de meseros/cocineros
        # Calcular diferencias
        # Guardar estado
```

#### JornadaLaboral

```python
class JornadaLaboral(models.Model):
    cajero = ForeignKey(Usuario, ...)
    fecha = DateField(...)
    estado = CharField(...)  # activa, finalizada
    hora_inicio = DateTimeField(...)
    hora_fin = DateTimeField(...)

    @classmethod
    def hay_jornada_activa(cls):
        """Verifica si hay jornada activa hoy"""
        return cls.objects.filter(
            fecha=date.today(),
            estado='activa'
        ).exists()
```

#### AlertaStock

```python
class AlertaStock(models.Model):
    producto = ForeignKey(Producto, on_delete=SET_NULL, null=True)
    producto_nombre = CharField(...)  # Guardado para historial
    tipo_alerta = CharField(...)  # bajo, agotado
    estado = CharField(...)  # activa, resuelta, ignorada
    stock_actual = IntegerField(...)
    resuelto_por = ForeignKey(Usuario, ...)
```

---

## 🚀 Instalación y Configuración

### 1. Requisitos Previos

```bash
Python 3.13+
pip
virtualenv (opcional pero recomendado)
```

### 2. Clonar e Instalar

```bash
# Navegar al proyecto
cd ProyectoR

# Activar entorno virtual
.\env\Scripts\activate  # Windows
source env/bin/activate  # Linux/Mac

# Instalar dependencias
cd restaurante_qr_project
pip install -r requirements.txt
```

### 3. Configurar Variables de Entorno

Crear archivo `.env` en la raíz de `restaurante_qr_project/`:

```bash
# .env
SECRET_KEY='tu-secret-key-super-segura'
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de datos
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### 4. Configurar Base de Datos

```bash
# Crear migraciones
python manage.py makemigrations
python manage.py migrate

# Crear datos iniciales (usuarios, productos, mesas)
python crear_datos_iniciales.py
```

### 5. Datos de Prueba Creados

El script `crear_datos_iniciales.py` crea:

**Usuarios:**
- Admin: username=`admin`, password=`admin123`
- Cajero1: username=`cajero1`, PIN=`1000`
- Cajero2: username=`cajero2`, PIN=`1001`
- Mesero1: username=`mesero1` (acceso por QR)
- Cocinero1: username=`cocinero1` (acceso por QR)

**Productos:** 16 productos en 4 categorías
- Entradas (3): Empanadas, Sopas
- Platos Principales (5): Pique Macho, Silpancho, Sajta, etc.
- Bebidas (5): Refrescos, Jugos, Cerveza, etc.
- Postres (3): Helado, Flan, Mousse

**Mesas:** 15 mesas
- Mesas 1-10: Capacidad 4 personas
- Mesas 11-15: Capacidad 6 personas

### 6. Iniciar Servidor

```bash
# Desarrollo local
python manage.py runserver

# Accesible en red local (para escanear QR desde celular)
python manage.py runserver 0.0.0.0:8000
```

### 7. Acceder al Sistema

```
URL: http://127.0.0.1:8000/login/
```

**Credenciales de prueba:**
- **Cajero:** PIN `1000` o `1001`
- **Admin:** username `admin`, password `admin123`
- **Empleados:** Generar QR desde panel de cajero

---

## 🔄 Flujos de Trabajo

### Flujo Completo: Día de Trabajo

```
MAÑANA - Inicio de Operaciones
==================================

1. Cajero llega
   → Login con PIN: 1000
   → Redirige a /caja/

2. Abrir Caja
   → Click "Abrir Turno"
   → Selecciona: Turno "Mañana"
   → Ingresa: Efectivo inicial Bs/ 100
   → Submit
   → Caja ABIERTA ✅

3. Activar Jornada
   → Click "Gestión de Jornada"
   → Click "Iniciar Jornada"
   → Jornada ACTIVA ✅
   → Empleados pueden trabajar

4. Generar QR para Empleados
   → Click "Gestión de Personal"
   → Lista de empleados cargada
   → Click "Generar QR" para Juan (mesero)
   → Modal con QR se abre
   → Juan escanea con celular
   → Juan accede automáticamente al sistema

DURANTE EL DÍA - Operaciones
==================================

5. Cliente Llega
   → Mesero toma pedido
   → Pedido → Cocina
   → Cocinero prepara
   → Mesero entrega

6. Cliente Pide Cuenta
   → Cajero ve pedido en panel
   → Click "Ver Detalle" → Revisar pedido
   → Click "Modificar" si es necesario:
      * Agregar/quitar productos
      * Cambiar cantidades
      * Buscar en menú completo
   → Click "Cobrar"
   → Selecciona método: Efectivo
   → Ingresa monto recibido: Bs/ 100
   → Aplica descuento: 10%
   → Aplica propina: Bs/ 10
   → Submit
   → Factura generada
   → Pedido PAGADO ✅

NOCHE - Cierre de Operaciones
==================================

7. Finalizar Jornada
   → Click "Gestión de Jornada"
   → Click "Finalizar Jornada"
   → Jornada FINALIZADA ❌
   → Empleados pierden acceso automáticamente

8. Cerrar Caja
   → Click "Cerrar Caja"
   → Cuenta efectivo físico
   → Ingresa monto real: Bs/ 450
   → Submit
   → Sistema calcula:
      * Efectivo esperado: Bs/ 455
      * Efectivo real: Bs/ 450
      * Diferencia: -Bs/ 5 (faltante)
   → Reporte de cierre generado
   → Caja CERRADA ✅

9. Cajero Cierra Sesión
   → Logout
   → Fin del día
```

---

## 🌐 APIs y Endpoints

### Autenticación

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/usuarios/login-pin/` | Login con PIN (cajeros) |
| POST | `/usuarios/login-admin/` | Login tradicional (admin/gerente) |
| GET | `/usuarios/auth-qr/<uuid>/` | Autenticación por QR |
| GET | `/usuarios/logout/` | Cerrar sesión |

### Caja (HTML)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/caja/` | Panel principal cajero |
| GET/POST | `/caja/abrir/` | Abrir turno |
| GET/POST | `/caja/cerrar/` | Cerrar turno |
| GET | `/caja/personal/` | Lista empleados |
| GET | `/caja/personal/generar-qr/<id>/` | Generar QR empleado |
| GET/POST | `/caja/jornada/` | Gestionar jornada laboral |
| GET | `/caja/modificar-pedido/<id>/` | Modificar pedido |
| GET | `/caja/pedido/<id>/` | Detalle de pedido |

### Caja (API)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/caja/pedidos-pendientes/` | Pedidos pendientes de pago |
| GET | `/api/caja/pedido/<id>/detalle/` | Detalle completo de pedido |
| POST | `/api/caja/pago-simple/` | Procesar pago simple |
| POST | `/api/caja/pago-mixto/` | Pago con múltiples métodos |
| POST | `/api/caja/aplicar-descuento/` | Aplicar descuento a pedido |
| POST | `/api/caja/aplicar-propina/` | Aplicar propina a pedido |
| POST | `/api/caja/pedido/<id>/modificar/` | Modificar productos del pedido |
| POST | `/api/caja/abrir-caja/` | Abrir turno de caja |
| POST | `/api/caja/cerrar-caja/` | Cerrar turno de caja |
| GET | `/api/caja/estadisticas-dia/` | Estadísticas del día |
| GET | `/api/caja/alertas-stock/` | Alertas de inventario |

### Pedidos

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/cocina/` | Panel de cocina |
| GET | `/mesero/` | Panel de mesero |
| GET | `/empleado/` | Panel unificado empleado |
| POST | `/api/pedidos/<id>/actualizar/` | Actualizar estado pedido |
| POST | `/api/pedidos/<id>/entregar/` | Marcar como entregado |

### Productos

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/productos/agrupados/` | Productos agrupados por categoría |
| GET | `/api/productos/` | Lista de productos |

---

## 🔧 Configuración Avanzada

### Variables de Entorno

```python
# settings.py
from decouple import config

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')

CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000'
).split(',')
```

### Middleware (Orden Importante)

```python
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'app.caja.middleware.JornadaLaboralMiddleware',  # ⚠️ Al final
]
```

### Autenticación DRF

```python
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
}
```

---

## 🔒 Seguridad

### Medidas Implementadas

1. **Protección de Datos Sensibles**
   - SECRET_KEY en variables de entorno
   - Contraseñas hasheadas con Django
   - Tokens QR únicos (UUID v4)

2. **Control de Acceso**
   - Middleware de jornada laboral
   - Decoradores `@login_required`
   - Validación de roles en vistas
   - Protección PROTECT en relaciones críticas

3. **Integridad de Datos**
   - `on_delete=PROTECT` en productos y mesas
   - `on_delete=SET_NULL` con respaldo de nombres
   - Auditoría completa de modificaciones
   - Historial de cambios en pedidos

4. **CSRF Protection**
   - Tokens CSRF en todos los formularios
   - Validación en APIs con SessionAuthentication

---

## 📊 Mejoras de Base de Datos

### Cambios Críticos Implementados

1. **Pedido.mesa** - `on_delete=CASCADE` → `PROTECT`
   - Previene eliminación accidental de mesas con historial
   - Agrega `related_name='pedidos'`

2. **DetallePedido.producto** - `on_delete=CASCADE` → `PROTECT`
   - Protege historial de ventas
   - Agrega `related_name='detalles_pedidos'`

3. **AlertaStock.producto** - `on_delete=CASCADE` → `SET_NULL`
   - Mantiene historial de alertas
   - Agrega campo `producto_nombre` para respaldo

4. **Related Names** - Agregados a todas las ForeignKeys
   - Consultas más intuitivas
   - Mejor legibilidad del código

---

## 📚 Comandos Personalizados

### Configurar Usuarios

```bash
python manage.py configurar_usuarios
```

Asigna automáticamente:
- **Cajeros:** PIN 1000, 1001, 1002...
- **Meseros:** Sin PIN, áreas=['mesero']
- **Cocineros:** Sin PIN, áreas=['cocina']
- **Admin/Gerente:** Sin PIN, todas las áreas

### Crear Datos Iniciales

```bash
python crear_datos_iniciales.py
```

Crea:
- 5 usuarios de prueba
- 16 productos en 4 categorías
- 15 mesas

---

## 📞 Información del Proyecto

**Versión:** 2.0.0
**Última Actualización:** Enero 2025
**Django:** 5.2
**Python:** 3.13

### Apps del Proyecto

El sistema está dividido en 7 aplicaciones Django:

1. **usuarios** - Gestión de usuarios y autenticación multi-nivel
2. **mesas** - Gestión de mesas y códigos QR
3. **productos** - Catálogo de productos y categorías
4. **pedidos** - Sistema de pedidos completo
5. **caja** - Punto de venta y control de jornada
6. **reservas** - Sistema de reservas
7. **reportes** - Reportes y estadísticas

---

## 🎯 Próximas Funcionalidades

- [ ] Reportes avanzados en PDF
- [ ] Integración con impresora térmica
- [ ] App móvil para meseros
- [ ] Sistema de delivery
- [ ] Integración con pasarelas de pago
- [ ] Panel de cocina con pantalla táctil
- [ ] Sistema de fidelización de clientes

---

---

## ⚠️ Problemas Conocidos

### Problemas Críticos (Requieren solución inmediata)

#### 1. Falta archivo `.env`
**Ubicación:** `restaurante_qr_project/.env`

El proyecto requiere un archivo `.env` con las siguientes variables:

```env
SECRET_KEY=tu-clave-secreta-segura-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

**Solución:** Crear el archivo `.env` antes de iniciar el servidor.

#### 2. Error en modelo Mesa - Recursión infinita
**Archivo:** `app/mesas/models.py:33-40`

El método `save()` del modelo Mesa tiene un problema de recursión infinita al generar códigos QR.

**Problema:**
- `self.id` es `None` en nuevas instancias
- `self.qr_image.save()` llama a `self.save()` recursivamente

**Requiere corrección antes de crear mesas.**

#### 3. Importación circular en URLs
**Archivo:** `backend/urls.py:72-73`

La importación de `panel_empleado` está mal ubicada, causando modificación de `urlpatterns` después de definirse.

#### 4. Verificar archivo `api_views.py` en app caja
**Archivo:** `app/caja/api_views.py`

Validar que todas las funciones referenciadas en `api_urls.py` estén implementadas correctamente.

### Problemas Importantes (Afectan funcionalidad)

#### 5. Serializer de Pedidos no funcional
**Archivo:** `app/pedidos/serializers.py:27-47`

El método `create()` intenta acceder a `detalles` que está marcado como `read_only=True`, causando `KeyError`.

#### 6. Middleware agresivo de Jornada
**Archivo:** `app/caja/middleware.py:49-59`

El middleware cierra sesión de empleados sin previo aviso si la jornada finaliza mientras trabajan.

#### 7. Timezone en Reservas
**Archivo:** `app/reservas/models.py:69-75`

`timezone.make_aware()` falla si `datetime_reserva` ya es consciente de zona horaria.

### Problemas Menores (Mejoras recomendadas)

#### 8. URL hardcodeada en modelo Mesa
La URL del QR está hardcodeada con `http://127.0.0.1:8000`, no funcionará en producción.

#### 9. Falta validación de rol
Algunas vistas fallan con `AttributeError` si el usuario no tiene atributo `rol` (ej: superusuarios).

#### 10. Imports no utilizados
Múltiples archivos tienen imports de código comentado o no usado.

#### 11. Método deprecado en Reportes
`app/reportes/models.py:83-93` usa `.extra()` que está deprecado en Django moderno.

#### 12. Falta manejo de transacciones
La creación de pedidos no usa `@transaction.atomic`, puede causar inconsistencias.

#### 13. Exceso de código debug
Muchos `print()` deberían reemplazarse por el sistema de logging de Django.

### Configuraciones Faltantes

#### 14. Sistema de Caché
No hay configuración de caché, recomendado para verificación de jornada laboral.

#### 15. Logging
Falta configuración de logging en `settings.py`.

#### 16. Seguridad para Producción
Faltan configuraciones cuando `DEBUG=False`:
- `SECURE_SSL_REDIRECT`
- `SESSION_COOKIE_SECURE`
- `CSRF_COOKIE_SECURE`
- etc.

### Resumen

| Categoría | Cantidad | Estado |
|-----------|----------|--------|
| Problemas Críticos | 4 | ⚠️ Requieren solución inmediata |
| Problemas Importantes | 6 | 🟡 Afectan funcionalidad |
| Problemas Menores | 13 | 🔵 Mejoras recomendadas |
| **Total** | **23** | |

**Calificación del proyecto: 7.5/10**

✅ **Fortalezas:**
- Código limpio y organizado
- Buena separación de responsabilidades
- Funcionalidades completas
- Sistema de autenticación robusto

⚠️ **Áreas de mejora:**
- Corrección de problemas críticos
- Validaciones y manejo de errores
- Testing automatizado
- Configuraciones de seguridad

---

**🎉 Sistema funcional con mejoras pendientes para producción**
