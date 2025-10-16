# 🍽️ Sistema de Gestión Integral para Restaurantes (SGIR)

> Sistema completo de gestión para restaurantes con QR, comandas, reservas, caja y reportes.

[![Django](https://img.shields.io/badge/Django-5.2-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![SQLite](https://img.shields.io/badge/SQLite-3-lightgrey.svg)](https://www.sqlite.org/)
[![Version](https://img.shields.io/badge/Version-2.0.0-brightgreen.svg)](./CHANGELOG.md)

## 📋 Tabla de Contenidos

- [Características Principales](#-características-principales)
- [Tecnologías](#-tecnologías-utilizadas)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación](#-instalación)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Módulos del Sistema](#-módulos-del-sistema)
- [Características Implementadas](#-características-implementadas)
- [Testing](#-testing)
- [Uso del Sistema](#-uso-del-sistema)
- [API REST](#-api-rest)
- [Licencia](#-licencia)

---

## ✨ Características Principales

### 🎯 Funcionalidades Clave

1. **Sistema de Comandas con Mesero**
   - Registro del mesero que toma el pedido
   - Número de personas en la mesa
   - Información visible en cocina y caja

2. **Mesas Combinadas Automáticas**
   - Unión inteligente de mesas para grupos grandes
   - Asignación automática según capacidad
   - Liberación automática al cobrar

3. **Gestión de Reservas**
   - Asignación automática de mesas
   - Combinación de mesas si es necesario
   - Estados: Pendiente, Confirmada, En Uso, Completada, Cancelada

4. **Módulo de Caja Completo**
   - Pagos mixtos (efectivo + tarjeta + QR + móvil)
   - Turnos de caja con apertura/cierre
   - Descuentos y propinas
   - Historial de transacciones
   - Alertas de stock bajo

5. **Panel de Cocina**
   - Vista en tiempo real de pedidos
   - Estados: Pendiente → En Preparación → Listo
   - Auto-actualización cada 15 segundos
   - Información completa de cada comanda

6. **Códigos QR por Mesa**
   - Generación automática de QR
   - Acceso directo al menú digital
   - Pedidos desde el cliente

7. **Sistema de Reportes**
   - Reportes diarios, semanales, mensuales
   - Análisis de ventas por producto
   - Productos más vendidos
   - Observaciones inteligentes automáticas

---

## 🛠️ Tecnologías Utilizadas

### Backend
- **Django 5.2** - Framework web principal
- **Django REST Framework 3.16** - API REST
- **Python 3.13** - Lenguaje de programación
- **SQLite** - Base de datos (desarrollo)

### Frontend
- **HTML5/CSS3** - Estructura y estilos
- **JavaScript Vanilla** - Interactividad
- **Fetch API** - Comunicación con backend

### Librerías Adicionales
- **qrcode** - Generación de códigos QR
- **Pillow** - Procesamiento de imágenes
- **python-dotenv** - Variables de entorno
- **django-cors-headers** - Manejo de CORS

---

## 📦 Requisitos Previos

- Python 3.13 o superior
- pip (gestor de paquetes de Python)
- Git (para clonar el repositorio)
- Navegador web moderno

---

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/KaradyGamer/Sistema-de-Gesti-n-Integral-para-Restaurantes-SGIR-.git
cd Sistema-de-Gesti-n-Integral-para-Restaurantes-SGIR-
cd restaurante_qr_project
```

### 2. Crear entorno virtual

**Windows:**
```bash
python -m venv env
env\\Scripts\\activate
```

**Linux/Mac:**
```bash
python3 -m venv env
source env/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Crear archivo `.env` en la raíz del proyecto:

```env
SECRET_KEY=django-insecure-tq5vwx-3ic+u2z46a89p5gb-0xj6ge=hzr5gmipxn7k2m4q8w9
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000
DATABASE_URL=sqlite:///db.sqlite3
```

### 5. Aplicar migraciones

```bash
python manage.py migrate
```

### 6. Crear datos iniciales (recomendado)

Para poblar el sistema con usuarios, productos y mesas de ejemplo:

```bash
python scripts/crear_datos_iniciales.py
```

Esto creará:
- Usuarios de prueba (admin, cajeros, meseros, cocineros)
- Categorías y productos de ejemplo
- 15 mesas configuradas con QR codes

Ver [scripts/README.md](restaurante_qr_project/scripts/README.md) para más detalles.

### 7. Crear superusuario (opcional)

Si prefieres crear tu propio admin manualmente:

```bash
python manage.py createsuperuser
```

### 8. Ejecutar servidor

```bash
python manage.py runserver
```

El sistema estará disponible en: `http://127.0.0.1:8000/`

---

## 📁 Estructura del Proyecto

```
restaurante_qr_project/
├── app/
│   ├── usuarios/          # Gestión de usuarios y roles
│   ├── productos/         # Catálogo de productos
│   ├── mesas/            # Gestión de mesas y QR
│   ├── pedidos/          # Sistema de pedidos
│   ├── caja/             # Módulo de caja y pagos
│   ├── reservas/         # Sistema de reservas
│   └── reportes/         # Reportes y estadísticas
├── backend/              # Configuración del proyecto
├── templates/            # Frontend (HTML/CSS/JS)
│   ├── html/            # Templates HTML organizados
│   ├── css/             # Estilos CSS
│   └── js/              # JavaScript
├── scripts/             # Scripts de utilidad y setup
│   ├── README.md        # Documentación de scripts
│   ├── crear_datos_iniciales.py
│   ├── crear_cajero.py
│   └── actualizar_mesas.py
├── media/               # Archivos multimedia
├── logs/               # Archivos de log
├── db.sqlite3          # Base de datos
└── manage.py           # Script de gestión Django
```

---

## 🎨 Módulos del Sistema

### 1. 👥 Usuarios
- **Roles**: Admin, Cajero, Mesero, Cocinero
- Autenticación con Django Session
- JWT para APIs
- Login con PIN (cajeros)
- Gestión de permisos por rol

### 2. 🍕 Productos
- Categorías de productos
- Control de inventario
- Stock mínimo y alertas
- Precios en Bolivianos (Bs/)

### 3. 🪑 Mesas
- Capacidad configurable
- Estados: Disponible, Ocupada, Reservada
- QR único por mesa
- **Sistema de combinación automática**
- Posición en mapa (x, y)

### 4. 📋 Pedidos
- Estados: Pendiente → En Preparación → Listo → Entregado
- **Registro de mesero que comanda**
- **Número de personas**
- Detalles por producto
- Observaciones
- Cálculo automático de totales

### 5. 💰 Caja
- Turnos de trabajo (mañana, tarde, completo)
- Apertura/cierre de caja
- Métodos de pago:
  - Efectivo
  - Tarjeta
  - QR
  - Pago Móvil
  - **Pagos mixtos** (combinación de métodos)
- Descuentos y propinas
- Historial de transacciones
- Cuadre de caja
- Modificación de pedidos
- Reasignación de mesas

### 6. 📅 Reservas
- Formulario web para clientes
- **Asignación automática de mesa**
- **Combinación de mesas para grupos grandes**
- Estados: Pendiente, Confirmada, En Uso, Completada, Cancelada
- Confirmación por carnet
- Consulta de reservas

### 7. 📊 Reportes
- Reportes automáticos:
  - Diarios
  - Semanales
  - Mensuales
  - Personalizados
- Análisis por producto
- Productos más vendidos
- **Observaciones inteligentes automáticas**
- Exportación (futuro: Excel/PDF)

---

## 🌟 Características Implementadas

### ✅ Sistema de Comandas Mejorado
```
Mesa 1
Personas: 4
Mesero: Juan Pérez
Pedido:
- 2x Hamburguesa Especial
- 4x Coca Cola
- 1x Ensalada César
Total: Bs/ 95.00
```

### ✅ Mesas Combinadas
```
Reserva para 8 personas:
→ Mesa 1 (4p) + Mesa 2 (4p)
→ Estado: RESERVADAS
→ Capacidad combinada: 8 personas
→ Se muestra como "Mesa 1+2"
```

### ✅ Estados Automáticos de Mesas

| Acción | Estado Anterior | Estado Nuevo |
|--------|----------------|--------------|
| Mesero comanda | Disponible | **Ocupada** |
| Cliente reserva | Disponible | **Reservada** |
| Cajero cobra | Ocupada/Reservada | **Disponible** |

### ✅ Liberación Inteligente
- Al cobrar, libera mesa individual O grupo completo
- Separa mesas combinadas automáticamente
- Actualiza disponibilidad en tiempo real

---

## 🧪 Testing

### Ejecutar Tests

```bash
# Todos los tests
python manage.py test

# Tests específicos
python manage.py test app.pedidos
python manage.py test app.caja
python manage.py test app.reservas

# Con verbosidad
python manage.py test --verbosity=2
```

### Cobertura de Tests

```bash
# Instalar coverage
pip install coverage

# Ejecutar con cobertura
coverage run --source='app' manage.py test

# Ver reporte
coverage report

# Generar HTML
coverage html
```

### Suite de Tests Incluida

- **35 tests automatizados**
- Cobertura de módulos críticos:
  - Pedidos (9 tests)
  - Caja (13 tests)
  - Reservas (13 tests)

---

## 📖 Uso del Sistema

### 👨‍🍳 Cocinero

1. **Acceder**: `/login/` → Seleccionar "Acceso CAJERO" → Ingresar PIN
2. **Ver pedidos**: Panel muestra pedidos pendientes y en preparación
3. **Cambiar estado**:
   - Pendiente → Clic en "🔥 Comenzar Preparación"
   - En Preparación → Clic en "✅ Marcar como Listo"
4. **Auto-actualización**: Cada 15 segundos

### 👨‍💼 Cajero

1. **Abrir turno**: `/caja/abrir/`
   - Elegir turno (mañana/tarde/completo)
   - Registrar efectivo inicial

2. **Cobrar pedido**:
   - Panel principal → Seleccionar pedido "Entregado"
   - Clic en "💰 Cobrar"
   - Elegir método de pago
   - Aplicar descuentos/propinas (opcional)
   - Confirmar pago

3. **Cerrar turno**: `/caja/cierre/`
   - Contar efectivo real
   - Sistema calcula diferencia
   - Generar reporte de cierre

### 🧑‍🤝‍🧑 Cliente (Reservas)

1. **Hacer reserva**: `/reservas/nueva/`
   - Llenar formulario
   - **Indicar número de personas**
   - Sistema asigna mesa automáticamente
   - Recibir confirmación

2. **Consultar reserva**: `/reservas/consultar/`
   - Ingresar número de carnet
   - Ver reservas activas
   - Cancelar si es necesario

### 📱 Cliente (Pedido por QR)

1. Escanear código QR de la mesa
2. Ver menú digital
3. Seleccionar productos
4. Enviar pedido
5. Pedido llega directamente a cocina

---

## 🔌 API REST

### Endpoints Principales

#### Pedidos
```
POST   /api/pedidos/crear/              # Crear pedido
GET    /api/pedidos/cocina/             # Lista para cocina
PATCH  /api/pedidos/{id}/actualizar/    # Cambiar estado
```

#### Caja
```
GET    /api/caja/pedidos-pendientes/    # Pedidos por cobrar
POST   /api/caja/procesar-pago/         # Procesar pago simple
POST   /api/caja/procesar-pago-mixto/   # Pago con múltiples métodos
POST   /api/caja/abrir/                 # Abrir turno
POST   /api/caja/cerrar/                # Cerrar turno
```

#### Reservas
```
GET    /api/reservas/mesas-disponibles/ # Mesas disponibles
POST   /api/reservas/{id}/cancelar/     # Cancelar reserva
POST   /api/reservas/{id}/confirmar/    # Confirmar reserva
```

### Autenticación

**Django Session** (HTML/JavaScript):
```javascript
fetch('/api/pedidos/cocina/', {
    headers: {
        'X-CSRFToken': getCsrfToken()
    }
})
```

**JWT** (Apps externas):
```http
Authorization: Bearer {token}
```

---

## 📝 Configuración Adicional

### Logging

El sistema genera logs automáticos en `logs/`:
- `django.log` - Log general (INFO, DEBUG)
- `errors.log` - Solo errores (ERROR, CRITICAL)

Rotación automática: 5MB por archivo, 5 backups

### Seguridad en Producción

Cuando `DEBUG=False`, se activan automáticamente:
- HTTPS obligatorio
- Cookies seguras
- HSTS
- XSS protection
- Content type nosniff

### Cache

Sistema de cache configurado (LocMemCache):
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
```

---

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'Añadir nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

---

## 📄 Licencia

Este proyecto es privado y de uso educativo/comercial.

---

## 👨‍💻 Autor

**Desarrollado con 💚 por el equipo de desarrollo**

---

## 📞 Soporte

Para reportar bugs o solicitar funcionalidades:
- Issues: [GitHub Issues](https://github.com/KaradyGamer/Sistema-de-Gesti-n-Integral-para-Restaurantes-SGIR-/issues)

---

## 🎯 Roadmap

### ✅ Completado (v1.0)
- Sistema de comandas con mesero
- Mesas combinadas automáticas
- Asignación automática en reservas
- Módulo de caja completo
- Panel de cocina en tiempo real
- Sistema de reservas
- Códigos QR por mesa
- Reportes automáticos
- Suite de 35 tests

### ✅ Completado (v2.0) - 2025-10-15
- 🗺️ **Mapa visual interactivo de mesas para meseros**
- 🔒 **Control de stock atómico (sin race conditions)**
- ✅ **Validaciones completas de negocio**
- 🎯 **Sistema de comandas mejorado**
- 📊 **Alertas automáticas de inventario**
- 🔐 **Validación de jornada laboral**
- ⚡ **Optimización de rendimiento**

### 🔜 Próximas Funcionalidades (v3.0)
- 📱 App móvil para meseros
- 🖨️ Integración con impresora térmica
- 🚚 Módulo de delivery
- 💳 Integración con pasarelas de pago
- 📧 Notificaciones por email/SMS
- 📊 Dashboard con gráficas avanzadas
- 🌐 Multi-idioma
- 📄 Paginación en listados
- 🔄 WebSockets para actualizaciones en tiempo real

---

**⭐ Si te gusta el proyecto, dale una estrella en GitHub!**
