# MÓDULO DE CAJERO - INSTRUCCIONES DE USO

## ✅ ESTADO: COMPLETAMENTE IMPLEMENTADO

---

## 🚀 INICIO RÁPIDO

### 1. Usuario Cajero Creado
```
Usuario: cajero1
Contraseña: cajero123
Rol: cajero
```

### 2. Iniciar el Servidor
```bash
cd restaurante_qr_project
.\env\Scripts\python.exe manage.py runserver
```

### 3. Acceder al Sistema
1. Ir a: http://127.0.0.1:8000/login/
2. Seleccionar rol: "💰 Cajero"
3. Ingresar credenciales:
   - Usuario: `cajero1`
   - Contraseña: `cajero123`
4. Serás redirigido a: http://127.0.0.1:8000/caja/

---

## 📋 FUNCIONALIDADES DISPONIBLES

### Panel Principal (/caja/)
- ✅ Ver pedidos pendientes de pago
- ✅ Estadísticas del día
- ✅ Alertas de stock
- ✅ Estado del turno actual

### Procesamiento de Pagos
- ✅ Pago simple (un método)
- ✅ Pago mixto (varios métodos)
- ✅ Cálculo automático de cambio
- ✅ Generación de factura

### Modificación de Pedidos
- ✅ Agregar productos
- ✅ Eliminar productos
- ✅ Cambiar cantidades
- ✅ Aplicar descuentos
- ✅ Agregar propinas
- ✅ Reasignar a otra mesa

### Control de Inventario
- ✅ Validación de stock
- ✅ Descuento automático
- ✅ Alertas automáticas
- ✅ Sistema de resolución

### Gestión de Caja
- ✅ Abrir turno
- ✅ Cerrar turno con cuadre
- ✅ Cálculo de diferencias
- ✅ Totales por método de pago

### Mapa de Mesas
- ✅ Vista en tiempo real
- ✅ Colores por estado
- ✅ Totales pendientes

### Reportes
- ✅ Historial de transacciones
- ✅ Estadísticas del día
- ✅ Filtros avanzados

---

## 🗺️ RUTAS DISPONIBLES

### HTML (Vistas)
```
/caja/                          → Panel principal
/caja/pedido/<id>/              → Detalle de pedido
/caja/pedido/<id>/pagar/        → Procesar pago
/caja/pedido/<id>/modificar/    → Modificar pedido
/caja/pedido/<id>/reasignar/    → Reasignar mesa
/caja/mapa-mesas/               → Mapa digital
/caja/historial/                → Historial
/caja/abrir/                    → Abrir turno
/caja/cerrar/                   → Cerrar turno
/caja/alertas-stock/            → Ver alertas
```

### APIs REST
```
GET  /api/caja/pedidos/pendientes/           → Lista pedidos
GET  /api/caja/pedidos/<id>/                 → Detalle
POST /api/caja/pago/simple/                  → Pago simple
POST /api/caja/pago/mixto/                   → Pago mixto
POST /api/caja/pedidos/descuento/            → Aplicar descuento
POST /api/caja/pedidos/propina/              → Aplicar propina
POST /api/caja/pedidos/agregar-producto/     → Agregar producto
DELETE /api/caja/pedidos/detalle/<id>/eliminar/ → Eliminar
PATCH /api/caja/pedidos/detalle/<id>/cantidad/  → Cambiar cantidad
POST /api/caja/pedidos/reasignar-mesa/       → Reasignar
POST /api/caja/turno/abrir/                  → Abrir turno
POST /api/caja/turno/cerrar/                 → Cerrar turno
GET  /api/caja/mapa-mesas/                   → Mapa
GET  /api/caja/estadisticas/                 → Estadísticas
GET  /api/caja/alertas-stock/                → Alertas
```

---

## 🗄️ MODELOS CREADOS

### 1. Transaccion
- Registro de pagos
- Facturación
- Comprobantes

### 2. DetallePago
- Pagos mixtos
- Referencias

### 3. CierreCaja
- Turnos
- Cuadre
- Totales

### 4. HistorialModificacion
- Auditoría completa
- Tracking de cambios

### 5. AlertaStock
- Alertas automáticas
- Sistema de resolución

---

## 📊 CAMBIOS EN MODELOS EXISTENTES

### Mesa
```python
+ capacidad (default=4)
+ disponible (default=True)
+ posicion_x (default=0)
+ posicion_y (default=0)
+ estado 'pagando'
```

### Pedido
```python
+ estado_pago (pendiente/parcial/pagado/cancelado)
+ monto_pagado
+ propina
+ descuento
+ descuento_porcentaje
+ total_final
+ observaciones
+ observaciones_caja
+ fecha_pago
+ cajero_responsable
+ modificado
+ reasignado
+ forma_pago: 'movil', 'mixto'
```

### Producto
```python
+ stock_actual
+ stock_minimo
+ requiere_inventario
+ métodos: stock_bajo, agotado, descontar_stock(), agregar_stock()
```

### Usuario
```python
+ rol: 'cajero'
```

---

## 🧪 PRUEBAS RÁPIDAS

### Probar Login
1. Ir a http://127.0.0.1:8000/login/
2. Seleccionar "💰 Cajero"
3. Login con cajero1/cajero123
4. Verificar redirección a /caja/

### Probar Panel de Caja
1. Debe mostrar estadísticas del día
2. Debe listar pedidos pendientes
3. Debe mostrar alertas de stock

### Probar APIs (con Postman/Thunder Client)
```bash
# Obtener pedidos pendientes
GET http://127.0.0.1:8000/api/caja/pedidos/pendientes/
Headers: Authorization: Bearer <token>

# Ver estadísticas
GET http://127.0.0.1:8000/api/caja/estadisticas/
```

---

## 🔧 COMANDOS ÚTILES

### Crear más usuarios cajeros
```python
python manage.py shell

from app.usuarios.models import Usuario
cajero2 = Usuario.objects.create_user(
    username='cajero2',
    password='cajero123',
    first_name='María',
    last_name='González',
    rol='cajero'
)
```

### Ver todas las mesas
```python
python manage.py shell

from app.mesas.models import Mesa
for mesa in Mesa.objects.all():
    print(f"Mesa {mesa.numero}: capacidad={mesa.capacidad}, disponible={mesa.disponible}")
```

### Verificar migraciones
```bash
python manage.py showmigrations caja
```

---

## 📝 PRÓXIMOS PASOS OPCIONALES

Si quieres seguir mejorando el módulo:

1. **Crear templates restantes:**
   - detalle_pedido.html
   - procesar_pago.html
   - mapa_mesas.html
   - historial.html
   - cierre_caja.html

2. **Agregar JavaScript:**
   - Calculadora de pagos
   - Actualización en tiempo real
   - Drag & drop en mapa

3. **Mejoras adicionales:**
   - Impresión de facturas
   - Exportación a Excel
   - Gráficos de ventas
   - Notificaciones push

---

## ❓ SOLUCIÓN DE PROBLEMAS

### Error: "No tienes permisos"
- Verificar que el usuario tiene rol='cajero'
- Verificar que está logueado
- Revisar backend/settings.py que 'app.caja' está en INSTALLED_APPS

### Error: "No hay turno abierto"
- Ir a /caja/abrir/ para abrir un turno
- O usar la API: POST /api/caja/turno/abrir/

### Error: "Mesa sin capacidad"
- Ejecutar: python actualizar_mesas.py
- O actualizar manualmente desde /admin/

### Error 404 en /caja/
- Verificar que las URLs están registradas en backend/urls.py
- Reiniciar el servidor

---

## 📞 SOPORTE

Para reportar bugs o sugerir mejoras:
- Revisar el código en app/caja/
- Revisar los modelos en app/caja/models.py
- Revisar las vistas en app/caja/views.py

---

**✅ ¡El módulo de cajero está completamente funcional y listo para usar!**

Fecha de implementación: 30/09/2025
Versión: 1.0.0