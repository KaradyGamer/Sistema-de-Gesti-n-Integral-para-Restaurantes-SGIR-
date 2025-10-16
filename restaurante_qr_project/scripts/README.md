# Scripts de Utilidad

Esta carpeta contiene scripts de setup y mantenimiento para el sistema.

## 📋 Scripts Disponibles

### 1. `crear_datos_iniciales.py`

Crea todos los datos iniciales necesarios para empezar a usar el sistema.

**¿Cuándo usar?**
- Primera vez que instalas el proyecto
- Después de resetear la base de datos
- Para crear datos de prueba/desarrollo

**¿Qué crea?**
- ✅ Usuarios (admin, cajeros, meseros, cocineros)
- ✅ Categorías de productos
- ✅ Productos de ejemplo
- ✅ Mesas (numeradas y configuradas)
- ✅ QR codes para cada mesa

**Cómo ejecutar:**
```bash
cd restaurante_qr_project
python scripts/crear_datos_iniciales.py
```

**Usuarios creados:**
- `admin` / `admin123` - Administrador con acceso total
- `cajero1` / `cajero123` (PIN: 1000)
- `cajero2` / `cajero123` (PIN: 2000)
- `mesero1` / `mesero123` (PIN: 3000)
- `mesero2` / `mesero123` (PIN: 4000)
- `cocinero1` / `cocinero123` (PIN: 5000)

---

### 2. `crear_cajero.py`

Crea un usuario cajero de prueba rápidamente.

**¿Cuándo usar?**
- Necesitas agregar un cajero rápido
- Testing rápido del módulo de caja

**¿Qué crea?**
- Usuario: `cajero1`
- Contraseña: `cajero123`
- Rol: Cajero

**Cómo ejecutar:**
```bash
cd restaurante_qr_project
python scripts/crear_cajero.py
```

---

### 3. `actualizar_mesas.py`

Actualiza mesas existentes con capacidad y posiciones para el mapa visual.

**¿Cuándo usar?**
- Después de agregar mesas manualmente al admin
- Si las mesas no tienen capacidad asignada
- Si el mapa de mesas no muestra las posiciones correctamente

**¿Qué hace?**
- Asigna capacidad por defecto (4 personas)
- Calcula posiciones X,Y para el mapa visual
- Distribuye mesas en grid 4x4

**Cómo ejecutar:**
```bash
cd restaurante_qr_project
python scripts/actualizar_mesas.py
```

---

## 🚀 Orden Recomendado para Setup Inicial

Si es la primera vez que configuras el proyecto:

```bash
# 1. Crear/migrar base de datos
python manage.py migrate

# 2. Crear todos los datos iniciales
python scripts/crear_datos_iniciales.py

# 3. (Opcional) Actualizar mesas si es necesario
python scripts/actualizar_mesas.py

# 4. Iniciar servidor
python manage.py runserver
```

## 📝 Notas

- Todos los scripts usan `django.setup()` para acceder a los modelos
- Son **idempotentes** - Puedes ejecutarlos múltiples veces sin problemas
- Si un registro ya existe, no lo duplican
- Puedes modificarlos para ajustar datos de prueba según necesites

## ⚠️ Advertencia

Estos scripts son para **desarrollo/testing**. En producción:
- No uses contraseñas simples como `admin123`
- Crea usuarios manualmente con contraseñas seguras
- Usa variables de entorno para credenciales
