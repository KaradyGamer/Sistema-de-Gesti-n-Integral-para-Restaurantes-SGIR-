# CHANGELOG - Sistema de Gestión Integral para Restaurantes (SGIR)

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
