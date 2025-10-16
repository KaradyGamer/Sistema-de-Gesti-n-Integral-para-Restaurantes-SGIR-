# CHANGELOG - Sistema de Gestión Integral para Restaurantes (SGIR)

## [2.1.0] - 2025-10-15

### ✨ NUEVAS CARACTERÍSTICAS

#### Sistema de Modificación de Pedidos con Control de Stock
- **[NUEVO]** Modificación completa de pedidos con rollback automático de inventario
  - Agregar nuevos productos al pedido
  - Eliminar productos no pagados del pedido
  - Cambiar cantidades de productos existentes
  - Stock se restaura automáticamente al eliminar/reducir productos
  - Stock se descuenta automáticamente al agregar/aumentar productos
  - Archivo: `app/pedidos/utils.py`

- **[NUEVO]** Control de pago por producto individual
  - Cada producto en un pedido puede ser pagado parcialmente
  - Campo `cantidad_pagada` en DetallePedido
  - Propiedad `cantidad_pendiente` calcula productos sin pagar
  - Propiedad `esta_pagado_completo` valida si producto fue pagado
  - Solo se pueden modificar productos NO pagados
  - Archivo: `app/pedidos/models.py:106-134`

- **[NUEVO]** Snapshot de precios históricos
  - Precio del producto se captura al momento del pedido
  - Campo `precio_unitario` en DetallePedido
  - Cambios futuros de precio no afectan pedidos existentes
  - Cálculos siempre usan precio histórico
  - Archivo: `app/pedidos/models.py:98-103`

#### APIs para Modificación de Pedidos
- **[NUEVO]** `POST /api/pedidos/<id>/modificar/` - Modificar pedido completo
  - Recibe dict de productos con cantidades nuevas
  - Restaura stock de productos eliminados
  - Descuenta stock de productos nuevos
  - Manejo de errores de stock insuficiente con rollback
  - Archivo: `app/pedidos/views.py:1003-1057`

- **[NUEVO]** `DELETE /api/pedidos/<id>/eliminar-producto/<producto_id>/` - Eliminar producto
  - Elimina solo cantidad NO pagada
  - Restaura stock automáticamente
  - Si producto está completamente pagado, devuelve error
  - Archivo: `app/pedidos/views.py:1060-1093`

- **[NUEVO]** `GET /api/pedidos/<id>/resumen-modificacion/` - Resumen previo a modificación
  - Muestra productos que pueden ser modificados
  - Indica cantidad pagada vs pendiente por producto
  - Muestra stock disponible de cada producto
  - Archivo: `app/pedidos/views.py:1096-1121`

### 🔧 MEJORAS TÉCNICAS

#### Modelos
- **[MEJORADO]** Modelo DetallePedido con campos de control de pago
  - `precio_unitario`: Snapshot del precio al momento del pedido
  - `cantidad_pagada`: Unidades ya pagadas del producto
  - `@property cantidad_pendiente`: Calcula unidades sin pagar
  - `@property esta_pagado_completo`: Validación de pago completo
  - Archivo: `app/pedidos/models.py:89-134`

- **[MEJORADO]** Modelo Pedido con métodos de cálculo de pagos
  - `calcular_total()`: Recalcula total desde detalles
  - `todos_productos_pagados()`: Valida si TODO está pagado
  - `productos_pendientes_pago()`: Lista productos sin pagar
  - Archivo: `app/pedidos/models.py:65-86`

#### Funciones Utilitarias
- **[NUEVO]** `modificar_pedido_con_stock()` - Modificación atómica con stock
  - Transacción completa con @transaction.atomic
  - Rollback automático si hay errores
  - Logging detallado de operaciones
  - Archivo: `app/pedidos/utils.py:14-144`

- **[NUEVO]** `eliminar_producto_de_pedido()` - Eliminación con validación
  - Verifica que producto no esté completamente pagado
  - Restaura solo cantidad pendiente
  - Si tiene cantidad pagada, reduce en lugar de eliminar
  - Archivo: `app/pedidos/utils.py:147-206`

- **[NUEVO]** `obtener_resumen_modificacion()` - Info detallada pre-modificación
  - Serializa información completa del pedido
  - Indica si cada producto puede ser modificado
  - Muestra stock disponible de cada producto
  - Archivo: `app/pedidos/utils.py:209-253`

### 📊 IMPACTO DE CAMBIOS

**Archivos Modificados**: 5
**Archivos Nuevos**: 1 (`app/pedidos/utils.py`)
**Líneas Agregadas**: ~500
**Migraciones**: 1 nueva (`0006_add_precio_unitario_and_cantidad_pagada_to_detalle`)

### 🔄 BREAKING CHANGES

Ninguno. Todos los cambios son retrocompatibles. Los campos nuevos tienen valores por defecto.

### 🧪 PRUEBAS RECOMENDADAS

1. Crear pedido nuevo y verificar que `precio_unitario` se captura
2. Modificar pedido agregando productos (verificar descuento de stock)
3. Modificar pedido eliminando productos (verificar restauración de stock)
4. Intentar modificar producto ya pagado (debe fallar)
5. Modificar pedido con stock insuficiente (debe hacer rollback)

---

## [2.0.0] - 2025-10-15

### 🔴 CORRECCIONES CRÍTICAS

#### Seguridad y Consistencia de Datos
- **[CRÍTICO]** Corregido race condition en descuento de stock de productos
  - Implementado descuento atómico usando F() expressions
  - Evita stock negativo en pedidos simultáneos
  - Archivo: `app/productos/models.py`

- **[CRÍTICO]** Implementado descuento automático de stock al crear pedidos
  - Stock se descuenta antes de crear el detalle del pedido
  - Rollback completo si stock insuficiente
  - Validación de inventario funcional
  - Archivo: `app/pedidos/views.py`

- **[CRÍTICO]** Validación de estado de mesa antes de crear pedido
  - Verifica que mesa esté disponible
  - Bloquea creación de doble pedido en misma mesa
  - Previene conflictos de estado
  - Archivo: `app/pedidos/views.py`

- **[CRÍTICO]** Validación completa de número de personas
  - Valida mínimo 1 persona
  - Verifica capacidad de mesa (individual o combinada)
  - Mensajes de error descriptivos
  - Archivo: `app/pedidos/views.py`

#### Performance y Optimización
- **[CRÍTICO]** Optimizada generación de código QR en mesas
  - QR solo se genera en mesa nueva o cuando no existe
  - Separado método `_generate_qr_code()` para evitar recursión
  - Mejora significativa de performance
  - Archivo: `app/mesas/models.py`

### 🟠 MEJORAS DE ALTA PRIORIDAD

#### Control de Acceso
- **[ALTO]** Validación de jornada laboral activa
  - Meseros no pueden crear pedidos sin jornada abierta
  - Error 403 si no hay jornada activa
  - Archivo: `app/pedidos/views.py`

#### Flujo de Negocio
- **[ALTO]** Confirmado funcionamiento de liberación automática de mesas
  - Mesas se liberan correctamente al procesar pago
  - Mesas combinadas se separan automáticamente
  - Ya estaba implementado en: `app/caja/api_views.py`

### ✨ NUEVAS CARACTERÍSTICAS

#### Sistema de Mapa de Mesas para Meseros
- **[NUEVO]** Vista de mapa visual de mesas
  - Grid responsivo con todas las mesas
  - Colores por estado: 🟢 Disponible, 🔴 Ocupada, 🟡 Reservada, 🔵 Pagando
  - Click en mesa disponible redirige a formulario
  - Archivo: `templates/mesero/mapa_mesas.html`

- **[NUEVO]** Formulario de pedido con mesa predeterminada
  - Mesa se oculta (viene del mapa)
  - Badge visual mostrando mesa seleccionada
  - Campo "Número de Personas" visible y requerido
  - Archivo: `templates/cliente/formulario.html`

- **[NUEVO]** Botón de acceso rápido en panel mesero
  - Botón "🗺️ Mapa de Mesas" en header
  - Estilos con gradiente morado
  - Archivo: `templates/mesero/panel_mesero.html`

#### Integración Usuario-Pedido
- **[NUEVO]** Captura automática de mesero en pedidos
  - Usuario autenticado se asocia al pedido
  - Campo `usuario_id` oculto en formulario
  - Envío automático con datos del pedido
  - Archivos: `templates/cliente/formulario.html`, `staticfiles/js/cliente/formulario.js`

### 🐛 CORRECCIONES DE BUGS

#### Mapa de Mesas Cajero
- **[CORREGIDO]** Mapa de mesas del cajero mostraba "No hay mesas"
  - Cambiado filtro de `disponible=True` a `.all()`
  - Ahora muestra TODAS las mesas igual que mesero
  - Archivo: `app/caja/views.py`, `app/caja/api_views.py`

### 📚 MEJORAS DE CÓDIGO

#### Alertas de Stock
- **[MEJORADO]** Creación automática de alertas de stock bajo
  - Se crea alerta cuando stock < mínimo
  - Tipo automático: 'stock_bajo' o 'agotado'
  - Archivo: `app/productos/models.py`

#### Logging
- **[MEJORADO]** Logging detallado en creación de pedidos
  - Stock restante registrado en logs
  - Información de mesero y personas
  - Mejor trazabilidad de operaciones
  - Archivo: `app/pedidos/views.py`

#### Validaciones
- **[MEJORADO]** Mensajes de error más descriptivos
  - Usuario recibe información exacta del problema
  - Códigos HTTP apropiados (400, 403, 404, 409)
  - Archivo: `app/pedidos/views.py`

### 🔧 CAMBIOS TÉCNICOS

#### Base de Datos
- Uso de F() expressions para operaciones atómicas
- Transacciones garantizadas con `@transaction.atomic`
- Rollback explícito en casos de error

#### APIs
- Validación temprana antes de crear registros
- Respuestas JSON estandarizadas
- Manejo robusto de excepciones

### 📊 IMPACTO DE CAMBIOS

**Archivos Modificados**: 10
**Archivos Nuevos**: 2
**Líneas Agregadas**: ~350
**Líneas Modificadas**: ~150

**Problemas Críticos Resueltos**: 6/6 (100%)
**Problemas Altos Resueltos**: 2/8 (25%)

### ⚠️ BREAKING CHANGES

Ninguno. Todos los cambios son retrocompatibles.

### 🚀 PRÓXIMAS MEJORAS PLANIFICADAS

- Optimización de queries N+1 en APIs
- Paginación en listados largos
- Auto-actualización del mapa de mesas
- Optimización de imágenes de productos
- Índices en base de datos para campos frecuentes

---

## [1.0.0] - 2025-10-10

### Lanzamiento Inicial
- Sistema completo de gestión de restaurante
- Módulos: Pedidos, Caja, Mesas, Productos, Reservas, Usuarios, Reportes
- Panel para Mesero, Cocinero, Cajero
- Sistema de autenticación multi-método (PIN, QR, JWT, Sesión)
- Mapa digital de mesas
- Control de inventario básico
- Reportes automáticos

---

**Formato**: Este changelog sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/)
**Versionado**: [Semantic Versioning](https://semver.org/lang/es/)
