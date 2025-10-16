# 🔍 ANÁLISIS EXHAUSTIVO DE FALLAS LÓGICAS DEL SISTEMA

**Fecha**: 2025-10-15
**Versión Analizada**: 2.0.0
**Analista**: Claude Code (Asistente IA)

---

## 📊 RESUMEN EJECUTIVO

**Total de Problemas Encontrados**: 18
- 🔴 **Críticos**: 5 (requieren atención inmediata)
- 🟠 **Altos**: 7 (pueden causar problemas serios)
- 🟡 **Medios**: 4 (inconsistencias menores)
- 🟢 **Bajos**: 2 (mejoras recomendadas)

---

## 🔴 FALLAS LÓGICAS CRÍTICAS

### **CRÍTICO #1: Mesa con PROTECT permite eliminar si no tiene pedidos**
**Archivo**: `app/pedidos/models.py:28`
**Código**:
```python
mesa = models.ForeignKey('mesas.Mesa', on_delete=models.PROTECT, related_name='pedidos')
```

**Problema**:
- `PROTECT` solo bloquea si HAY pedidos relacionados
- Si una mesa NO tiene pedidos activos, puede eliminarse
- Pero la mesa puede tener:
  - Reservas futuras asignadas
  - Estar combinada con otras mesas
  - Tener QR code impreso en restaurante
  - Historial de transacciones

**Escenario de Falla**:
```
1. Mesa 5 tiene reserva para mañana (estado='reservada')
2. No tiene pedidos ACTIVOS hoy
3. Admin elimina Mesa 5
4. ✅ Django permite (no hay pedidos relacionados)
5. ❌ Reserva queda huérfana (mesa=NULL por SET_NULL)
6. ❌ Mañana cliente llega y no hay mesa asignada
```

**Impacto**: 🔥 ALTO - Pérdida de reservas, confusión operativa

**Solución Recomendada**:
```python
# Opción 1: No permitir eliminar mesas, solo desactivar
class Mesa(models.Model):
    disponible = models.BooleanField(default=True)
    eliminada = models.BooleanField(default=False)  # Soft delete

# Opción 2: Validar en delete() que no tenga reservas futuras
def delete(self, *args, **kwargs):
    from app.reservas.models import Reserva
    reservas_futuras = Reserva.objects.filter(
        mesa=self,
        estado__in=['pendiente', 'confirmada'],
        fecha_reserva__gte=timezone.now().date()
    ).exists()

    if reservas_futuras:
        raise ValidationError('No se puede eliminar mesa con reservas futuras')

    super().delete(*args, **kwargs)
```

---

### **CRÍTICO #2: Producto con PROTECT puede eliminarse**
**Archivo**: `app/pedidos/models.py:69`
**Código**:
```python
producto = models.ForeignKey('productos.Producto', on_delete=models.PROTECT, related_name='detalles_pedidos')
```

**Problema Similar a #1**:
- Solo protege si hay DetallePedido relacionados
- Pero si el producto:
  - Tiene stock (inventario activo)
  - Tiene alertas de stock bajo
  - Está en análisis de reportes

**Puede eliminarse** si no tiene pedidos activos

**Impacto**: 🔥 MEDIO - Pérdida de datos de inventario

**Solución**: Soft delete en Producto también

---

### **CRÍTICO #3: Cambio de precio de producto NO afecta pedidos pendientes**
**Archivo**: `app/productos/models.py:13`
**Problema**: No hay snapshot de precio al momento del pedido

**Escenario de Falla**:
```
1. Cerveza cuesta Bs/ 15
2. Cliente pide 5 cervezas (total: Bs/ 75)
3. Admin cambia precio a Bs/ 20
4. Cliente llega a pagar
5. ❓ ¿Paga Bs/ 75 o Bs/ 100?
```

**Estado Actual**:
```python
# DetallePedido.subtotal se calcula en crear_pedido_cliente:
subtotal = producto.precio * cantidad  # Guarda subtotal fijo ✅
```

**Análisis**: ✅ PARCIALMENTE CORRECTO
- El subtotal SÍ se guarda al crear el pedido
- El total del pedido también se guarda
- PERO: No se guarda el precio unitario histórico

**Riesgo**: Si se modifica el pedido (agregar/quitar productos), ¿qué precio se usa?

**Mejora Recomendada**:
```python
class DetallePedido(models.Model):
    pedido = models.ForeignKey(...)
    producto = models.ForeignKey(...)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)  # ⭐ NUEVO
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        if not self.precio_unitario:
            self.precio_unitario = self.producto.precio  # Snapshot
        if not self.subtotal:
            self.subtotal = self.precio_unitario * self.cantidad
        super().save(*args, **kwargs)
```

---

### **CRÍTICO #4: Cierre de jornada sin validar pedidos sin pagar**
**Archivo**: `app/caja/models.py` - CierreCaja
**Problema**: No hay validación que impida cerrar jornada con pedidos pendientes de pago

**Escenario de Falla**:
```
1. Turno de mañana: 10 pedidos, 8 pagados, 2 pendientes
2. Cajero cierra caja sin revisar
3. ✅ Sistema permite cerrar
4. ❌ Pedidos pendientes quedan "huérfanos"
5. ❌ Turno tarde no sabe si debe cobrarlos
6. ❌ Reporte de cierre incorrecto
```

**Impacto**: 🔥 MUY ALTO - Pérdida de dinero, reportes incorrectos

**Solución Recomendada**:
```python
# En api_views.py - cerrar_caja()
pedidos_pendientes = Pedido.objects.filter(
    estado_pago__in=['pendiente', 'parcial'],
    estado='entregado',  # Ya se entregó pero no se pagó
    fecha__date=cierre.fecha
).count()

if pedidos_pendientes > 0:
    return Response({
        'error': f'No se puede cerrar caja. Hay {pedidos_pendientes} pedidos pendientes de pago.',
        'pedidos_pendientes': pedidos_pendientes
    }, status=400)
```

---

### **CRÍTICO #5: Mesa "disponible" puede tener pedido "entregado" sin pagar**
**Problema**: Inconsistencia de estados

**Flujo Actual**:
```
1. Crear pedido → Mesa = 'ocupada' ✅
2. Cocina prepara → Pedido = 'listo' ✅
3. Mesero entrega → Pedido = 'entregado' ✅
4. ❓ Mesa sigue 'ocupada'? ✅ SÍ
5. Cajero cobra → Pedido = 'pagado' ✅
6. ❓ Mesa vuelve 'disponible'? ✅ SÍ (en api_views.py)
```

**Análisis**: ✅ FLUJO CORRECTO implementado

**PERO**: ¿Qué pasa si mesero marca "entregado" por error y cliente aún está comiendo?

**Pregunta para el usuario**:
> ¿El estado "entregado" significa que el cliente YA puede pagar, o que el mesero llevó la comida pero cliente sigue comiendo?

**Recomendación**: Agregar estado intermedio
```python
ESTADO_CHOICES = [
    ('pendiente', 'Pendiente'),
    ('en preparacion', 'En Preparación'),
    ('listo', 'Listo'),
    ('entregado', 'Entregado'),
    ('consumiendo', 'Cliente Consumiendo'),  # ⭐ NUEVO
    ('solicitando_cuenta', 'Cliente Pidió Cuenta'),  # ⭐ NUEVO
]
```

---

## 🟠 PROBLEMAS ALTOS

### **ALTO #6: Usuario eliminado/desactivado con pedidos asignados**
**Archivo**: `app/pedidos/models.py:46, 49`
**Código**:
```python
cajero_responsable = models.ForeignKey(..., on_delete=models.SET_NULL, null=True)
mesero_comanda = models.ForeignKey(..., on_delete=models.SET_NULL, null=True)
```

**Problema**: `SET_NULL` permite eliminar usuario, pero:
- Pedidos activos quedan sin responsable
- Reportes pierden información de quién atendió
- Auditoría incompleta

**Escenario**:
```
1. Mesero Juan toma 5 pedidos hoy
2. Admin elimina a Juan (renuncia)
3. ✅ Django pone mesero_comanda=NULL
4. ❌ No se sabe quién tomó esos pedidos
5. ❌ Reportes de performance incompletos
```

**Solución**: Soft delete en Usuario
```python
class Usuario(AbstractUser):
    activo = models.BooleanField(default=True)
    fecha_eliminacion = models.DateTimeField(null=True, blank=True)

    def delete(self, *args, **kwargs):
        # No eliminar físicamente
        self.activo = False
        self.fecha_eliminacion = timezone.now()
        self.save()
```

---

### **ALTO #7: Reserva en mesa "ocupada" permite crearse**
**Archivo**: `app/reservas/` - Sin validación aparente

**Problema**: No hay validación que impida crear reserva en mesa ya ocupada

**Escenario**:
```
1. Mesa 5 tiene pedido activo (ocupada)
2. Cliente hace reserva para hoy 20:00 en Mesa 5
3. ✅ Sistema permite (no hay validación)
4. ❌ A las 20:00 mesa sigue ocupada
5. ❌ Cliente reservado llega y no tiene mesa
```

**Solución**: Validar en crear_reserva
```python
if mesa.estado != 'disponible':
    # Verificar si estará disponible a la hora de la reserva
    pedidos_activos = Pedido.objects.filter(
        mesa=mesa,
        estado__in=['pendiente', 'en preparacion', 'listo', 'entregado']
    ).exists()

    if pedidos_activos:
        raise ValidationError(f'Mesa {mesa.numero} está actualmente ocupada')
```

---

### **ALTO #8: Dos meseros pueden ocupar misma mesa simultáneamente**
**Archivo**: `app/pedidos/views.py:124-139`
**Estado**: ✅ YA CORREGIDO en v2.0.0

**Código Actual**:
```python
if mesa.estado != 'disponible':
    return Response({'error': '...'}, status=400)

pedido_existente = Pedido.objects.filter(
    mesa=mesa,
    estado__in=['pendiente', 'en preparacion', 'listo']
).exists()
```

**Análisis**: ✅ CORRECTO - Valida estado y pedido existente

**PERO**: ¿Qué pasa con concurrencia?
```
Tiempo 0: Mesero A verifica mesa 5 → disponible ✅
Tiempo 1: Mesero B verifica mesa 5 → disponible ✅
Tiempo 2: Mesero A crea pedido → mesa = ocupada
Tiempo 3: Mesero B crea pedido → ❌ Debería fallar
```

**Solución**: Usar select_for_update()
```python
with transaction.atomic():
    mesa = Mesa.objects.select_for_update().get(numero=mesa_id)

    if mesa.estado != 'disponible':
        return Response({'error': '...'}, status=400)

    # Resto del código...
```

---

### **ALTO #9: Mesas combinadas sin transacción atómica**
**Archivo**: `app/mesas/utils.py` - funciones `combinar_mesas()` y `separar_mesas()`

**Problema**: Si falla a mitad de combinación, quedan inconsistentes

**Solución**: Agregar `@transaction.atomic`
```python
from django.db import transaction

@transaction.atomic
def combinar_mesas(mesas_list, estado='reservada'):
    # código actual...
```

---

### **ALTO #10: Stock puede quedar negativo en rollback parcial**
**Archivo**: `app/pedidos/views.py:207-224`
**Código Actual**:
```python
stock_descontado = producto.descontar_stock(cantidad)

if not stock_descontado:
    pedido.delete()  # Rollback
    mesa.estado = 'disponible'
    mesa.save()
    return Response({'error': '...'}, status=400)
```

**Problema**: ¿Qué pasa si YA se descontó stock de 3 productos y el 4to falla?

**Escenario**:
```
Pedido: Pizza (stock ok), Pasta (stock ok), Cerveza (stock ok), Postre (SIN STOCK)
1. Pizza: stock 10 → 9 ✅
2. Pasta: stock 5 → 4 ✅
3. Cerveza: stock 20 → 19 ✅
4. Postre: stock 0 → FALLA ❌
5. pedido.delete() se ejecuta
6. ❓ ¿Se restaura stock de Pizza, Pasta, Cerveza?
```

**Respuesta**: ❌ NO - El stock NO se restaura automáticamente

**Impacto**: Stock queda descontado sin pedido

**Solución**: Implementar rollback manual de stock
```python
productos_descontados = []

for item in productos_data:
    producto = Producto.objects.get(id=producto_id)
    stock_descontado = producto.descontar_stock(cantidad)

    if not stock_descontado:
        # RESTAURAR stock de productos anteriores
        for prod, cant in productos_descontados:
            prod.agregar_stock(cant)

        pedido.delete()
        mesa.estado = 'disponible'
        mesa.save()
        return Response({'error': '...'}, status=400)

    productos_descontados.append((producto, cantidad))
```

---

### **ALTO #11: Pago parcial sin validar monto**
**Archivo**: `app/caja/api_views.py` - procesar_pago

**Problema**: No valida que pago parcial sea menor que total

**Escenario**:
```
Total pedido: Bs/ 100
Cliente "paga parcial": Bs/ 150 ❌
Sistema acepta
```

**Solución**: Validar en API
```python
if estado_pago == 'parcial':
    if monto_pagado >= total_final:
        return Response({
            'error': 'Pago parcial debe ser menor que el total'
        }, status=400)
```

---

### **ALTO #12: Producto descontado puede quedar con stock negativo en race condition INTERNA**
**Archivo**: `app/productos/models.py:49-53`
**Código Actual** (ya corregido):
```python
updated = Producto.objects.filter(
    id=self.id,
    stock_actual__gte=cantidad
).update(stock_actual=F('stock_actual') - cantidad)
```

**Análisis**: ✅ CORRECTO - Usa F() expression

**PERO**: ¿Qué pasa si entre el `.filter()` y el `.update()` otro proceso cambia el stock?

**Respuesta**: ✅ NO HAY PROBLEMA - `F()` expression es atómica a nivel de base de datos

**Estado**: ✅ CORRECTO

---

## 🟡 PROBLEMAS MEDIOS

### **MEDIO #13: Total de pedido puede no coincidir con suma de detalles**
**Archivo**: `app/pedidos/views.py:194-196`
**Código**:
```python
pedido.total = total_calculado
pedido.save()
```

**Problema**: Si se modifican detalles después (agregar/quitar productos), total queda desactualizado

**Solución**: Usar método en modelo
```python
class Pedido(models.Model):
    # ...

    def calcular_total(self):
        """Calcula total desde detalles"""
        return sum(d.subtotal for d in self.detalles.all())

    def save(self, *args, **kwargs):
        if self.pk:  # Si ya existe, recalcular
            self.total = self.calcular_total()
        super().save(*args, **kwargs)
```

---

### **MEDIO #14: Reserva vencida no se marca automáticamente**
**Archivo**: `app/reservas/models.py:77-86`

**Problema**: Método `esta_vencida()` existe pero no se ejecuta automáticamente

**Solución**: Tarea programada (Celery)
```python
from celery import shared_task

@shared_task
def marcar_reservas_vencidas():
    reservas_vencidas = Reserva.objects.filter(
        estado='confirmada',
        fecha_reserva__lt=timezone.now().date()
    )

    for reserva in reservas_vencidas:
        if reserva.esta_vencida():
            reserva.estado = 'no_show'
            reserva.save()
```

---

### **MEDIO #15: QR de mesa puede apuntar a URL incorrecta en producción**
**Archivo**: `app/mesas/models.py:67-74`
**Código**:
```python
try:
    domain = Site.objects.get_current().domain
    protocol = 'https' if settings.DEBUG is False else 'http'
except:
    domain = '127.0.0.1:8000'
    protocol = 'http'
```

**Problema**: Si falla `Site.objects.get_current()`, usa localhost

**Solución**: Usar variable de entorno
```python
from decouple import config

domain = config('SITE_DOMAIN', default='127.0.0.1:8000')
protocol = config('SITE_PROTOCOL', default='http')
```

---

### **MEDIO #16: Campos nullable innecesariamente**
**Ejemplos**:
- `Pedido.observaciones` = NULL o blank?
- `Pedido.observaciones_caja` = NULL o blank?

**Recomendación**: Usar `blank=True, default=''` en lugar de `null=True` para CharField/TextField

**Razón**: Evita dos estados vacíos (NULL vs '')

---

## 🟢 MEJORAS RECOMENDADAS

### **BAJO #17: Falta logging de operaciones críticas**
**Recomendación**: Agregar logs en:
- Cierre de caja
- Liberación de mesas
- Cambios de estado de pedidos

---

### **BAJO #18: Sin rate limiting en APIs públicas**
**Archivo**: `app/pedidos/views.py:55` - `crear_pedido_cliente`

**Problema**: `@permission_classes([AllowAny])` sin rate limit

**Solución**: Django Ratelimit
```python
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='10/m', method='POST')
@api_view(['POST'])
@permission_classes([AllowAny])
def crear_pedido_cliente(request):
    # ...
```

---

## ❓ PREGUNTAS PARA EL USUARIO

### **Pregunta #1: Flujo de "Entregado"**
> ¿El estado "entregado" significa:
> A) Mesero llevó comida y cliente puede pagar inmediatamente
> B) Mesero llevó comida pero cliente sigue comiendo (mesa aún ocupada)

**Importancia**: Define si mesa se libera al entregar o al pagar

---

### **Pregunta #2: Eliminación de Datos**
> ¿Necesitan mantener historial completo de:
> - Mesas eliminadas
> - Productos descontinuados
> - Usuarios que renunciaron

**Si SÍ**: Implementar soft delete en todos los modelos

---

### **Pregunta #3: Modificación de Pedidos**
> ¿Se permite modificar un pedido después de creado?
> - ¿Puede agregar productos?
> - ¿Puede quitar productos?
> - ¿Puede cambiar cantidades?

**Actual**: Hay función `modificar_pedido()` en caja pero no validaciones claras

---

### **Pregunta #4: Pagos Parciales**
> ¿Escenario de pago parcial?
> - Cliente paga parte y se va?
> - Cliente paga en dos momentos?
> - Varios clientes en misma mesa pagan por separado?

**Importancia**: Define lógica de liberación de mesa

---

### **Pregunta #5: Reservas Simultáneas**
> ¿Una mesa puede tener múltiples reservas el mismo día?
> - Reserva 12:00-14:00
> - Reserva 19:00-21:00

**Actual**: No hay validación de overlapping

---

## 📋 RESUMEN DE ACCIONES RECOMENDADAS

### **Inmediatas** (próxima semana):
1. ✅ Implementar soft delete en Usuario, Mesa, Producto
2. ✅ Validar cierre de caja con pedidos pendientes
3. ✅ Rollback manual de stock en crear_pedido
4. ✅ select_for_update() en ocupar mesa

### **Corto plazo** (próximo mes):
5. ✅ Agregar estado "consumiendo" en pedidos
6. ✅ Validar overlapping de reservas
7. ✅ Snapshot de precio en DetallePedido
8. ✅ Transacciones atómicas en mesas combinadas

### **Mediano plazo** (2-3 meses):
9. ✅ Tarea programada para reservas vencidas
10. ✅ Rate limiting en APIs públicas
11. ✅ Logging completo de operaciones
12. ✅ Campo precio_unitario histórico

---

**Fin del Análisis**
