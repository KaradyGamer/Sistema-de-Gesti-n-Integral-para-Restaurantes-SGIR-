# Sistema de Gestión Integral para Restaurantes (SGIR)

## 📋 Descripción

Sistema completo de gestión para restaurantes que integra:
- ✅ **Gestión de Mesas** - QR codes, combinación de mesas, mapas visuales
- ✅ **Sistema de Pedidos** - Clientes, meseros, cocina con estados en tiempo real
- ✅ **Control de Inventario** - Stock automático, alertas de productos agotados
- ✅ **Sistema de Reservas** - Asignación automática, tolerancia de 15 minutos
- ✅ **Módulo de Caja** - Transacciones, cierres de turno, jornadas laborales
- ✅ **Reportes Contables** - Ventas, productos más vendidos, análisis de rendimiento
- ✅ **Multi-usuario** - Roles (admin, cajero, mesero, cocinero, gerente)

## 🚀 Versión Actual

**v2.3.0** - Sistema completo con tolerancia de reservas y eliminación suave

## 🎯 Características Principales

### 1. Sistema de Mesas
- **QR Codes automáticos** para cada mesa
- **Mapa visual** de mesas en tiempo real
- **Combinación de mesas** para grupos grandes
- **Estados**: disponible, ocupada, reservada, pagando
- **Eliminación suave** - Historial completo de reservas

### 2. Sistema de Pedidos
- **Modificación de pedidos** con control de stock automático
- **Pago parcial** por producto
- **Snapshot de precios** históricos
- **Estados**: pendiente → en preparación → listo → entregado → solicitando cuenta
- **Asignación de meseros** a cada pedido
- **Control de personas** por mesa

### 3. Sistema de Reservas
- **Asignación automática** de mesas según capacidad
- **Tolerancia de 15 minutos** - Libera mesas automáticas por no-show
- **Validación de solapamiento** - No permite reservas duplicadas
- **Comando automático** para liberar mesas vencidas

### 4. Control de Inventario
- **Descuento automático** de stock al crear pedidos
- **Restauración automática** de stock al modificar/eliminar productos
- **Alertas de stock bajo** y productos agotados
- **Operaciones atómicas** con F() expressions

### 5. Módulo de Caja
- **Transacciones múltiples** - Efectivo, tarjeta, QR, móvil
- **Pagos mixtos** - Divide un pago en varios métodos
- **Cierres de turno** con validación de pedidos pendientes
- **Jornadas laborales** - Control de apertura/cierre
- **Historial de modificaciones** completo

### 6. Seguridad y Validaciones
- **Control de concurrencia** con select_for_update()
- **Validación de cierre de caja** - No permite cerrar con pedidos activos
- **Eliminación suave** en 4 modelos principales
- **Transacciones atómicas** en operaciones críticas

## 📦 Tecnologías

- **Backend**: Django 5.2
- **Base de Datos**: SQLite (desarrollo) / PostgreSQL (producción)
- **API**: Django REST Framework
- **Autenticación**: JWT + Django Sessions
- **Frontend**: HTML, CSS, JavaScript vanilla
- **QR Codes**: qrcode library
- **Admin**: django-admin-interface (personalizado)

## 🛠️ Instalación

### Requisitos Previos
- Python 3.10+
- pip
- Entorno virtual (recomendado)

### Pasos de Instalación

1. **Clonar el repositorio**
```bash
git clone <repositorio>
cd restaurante_qr_project
```

2. **Crear entorno virtual**
```bash
python -m venv env
```

3. **Activar entorno virtual**
```bash
# Windows
env\Scripts\activate

# Linux/Mac
source env/bin/activate
```

4. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

5. **Configurar variables de entorno**

Crear archivo `.env` en la raíz del proyecto:
```env
SECRET_KEY=tu_clave_secreta_aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

6. **Aplicar migraciones**
```bash
python manage.py migrate
```

7. **Crear superusuario**
```bash
python manage.py createsuperuser
```

8. **Configurar usuarios de prueba** (opcional)
```bash
python manage.py configurar_usuarios
```

9. **Ejecutar servidor**
```bash
python manage.py runserver
```

10. **Acceder al sistema**
- Admin: http://localhost:8000/admin/
- Sistema: http://localhost:8000/

## 📚 Estructura del Proyecto

```
restaurante_qr_project/
├── app/
│   ├── usuarios/          # Gestión de usuarios y roles
│   ├── mesas/             # Mesas, QR codes, combinaciones
│   ├── productos/         # Productos y categorías
│   ├── pedidos/           # Pedidos y detalles
│   ├── reservas/          # Sistema de reservas
│   ├── caja/              # Transacciones y cierres
│   └── reportes/          # Reportes y análisis
├── backend/               # Configuración Django
├── templates/             # Plantillas HTML
├── staticfiles/           # Archivos estáticos (CSS, JS)
├── media/                 # Archivos subidos (imágenes, QR)
├── logs/                  # Logs del sistema
├── CHANGELOG.md           # Historial de cambios
├── ANALISIS_FALLAS_LOGICAS.md  # Análisis de fallas
└── manage.py              # Comando de Django
```

## 🔐 Roles y Permisos

### Admin
- Acceso completo al sistema
- Configuración de usuarios
- Gestión de mesas y productos

### Cajero
- Módulo de caja
- Transacciones y pagos
- Cierre de turnos
- Reportes

### Mesero
- Panel de pedidos (listos, entregados)
- Gestión de reservas
- Mapa de mesas
- Crear/modificar pedidos

### Cocinero
- Panel de cocina
- Actualizar estados de pedidos
- Ver pedidos pendientes y en preparación

### Gerente
- Acceso a todos los módulos
- Reportes avanzados
- Dashboard completo

## 🎮 Uso del Sistema

### Crear un Pedido

1. **Como Cliente (QR)**:
   - Escanear QR de la mesa
   - Seleccionar productos
   - Confirmar pedido

2. **Como Mesero**:
   - Acceder a mapa de mesas
   - Seleccionar mesa
   - Crear pedido con número de personas
   - Asignar productos

### Modificar un Pedido

```python
# API Endpoint
POST /api/pedidos/<id>/modificar/

# Body
{
    "productos": {
        "1": 3,  # producto_id: cantidad
        "2": 1
    }
}
```

### Liberar Mesas por No-Show

```bash
# Manual
python manage.py liberar_mesas_no_show

# Con tiempo personalizado
python manage.py liberar_mesas_no_show --minutos 20

# Automatizar con Task Scheduler (cada 10-15 min)
```

### Eliminar Suavemente

```python
# Eliminar producto (soft delete)
producto = Producto.objects.get(id=1)
producto.eliminar_suave(usuario=request.user)

# Restaurar
producto.restaurar()

# Filtrar solo activos
productos = Producto.objects.filter(activo=True)
```

## 📊 Comandos Útiles

### Gestión de Base de Datos
```bash
# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Ver estado de migraciones
python manage.py showmigrations
```

### Usuarios
```bash
# Configurar usuarios de prueba
python manage.py configurar_usuarios

# Crear superusuario
python manage.py createsuperuser
```

### Mantenimiento
```bash
# Liberar mesas vencidas
python manage.py liberar_mesas_no_show

# Recopilar archivos estáticos
python manage.py collectstatic

# Crear respaldo de BD
python manage.py dumpdata > backup.json
```

## 🐛 Resolución de Problemas

### Error: "No module named 'django'"
```bash
# Activar entorno virtual
env\Scripts\activate  # Windows
source env/bin/activate  # Linux/Mac

# Reinstalar dependencias
pip install -r requirements.txt
```

### Error: "Secret key not found"
```bash
# Crear archivo .env con SECRET_KEY
echo "SECRET_KEY=tu_clave_secreta" > .env
```

### Error: "Port already in use"
```bash
# Usar otro puerto
python manage.py runserver 8080
```

## 🔄 Actualización de Versión

```bash
# Ver versión actual
cat VERSION

# Aplicar nuevas migraciones
python manage.py migrate

# Reiniciar servidor
```

## 📖 Documentación Adicional

- **CHANGELOG.md** - Historial completo de cambios por versión
- **ANALISIS_FALLAS_LOGICAS.md** - Análisis técnico del sistema

## 🤝 Contribuciones

Sistema desarrollado para gestión integral de restaurantes.

## 📝 Licencia

Sistema propietario - Todos los derechos reservados

## 📞 Soporte

Para problemas o consultas, revisar la documentación en CHANGELOG.md

---

**Versión:** 2.3.0
**Última Actualización:** Octubre 2025
**Estado:** Producción-Ready ✅
