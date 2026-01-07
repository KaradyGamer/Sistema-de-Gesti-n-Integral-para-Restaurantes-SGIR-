from django.contrib import admin
from .models import Transaccion, DetallePago, CierreCaja, HistorialModificacion, AlertaStock


@admin.register(Transaccion)
class TransaccionAdmin(admin.ModelAdmin):
    """
    Administración de transacciones de pago del sistema.

    Gestiona el registro completo de todas las transacciones financieras,
    incluyendo información de facturación, métodos de pago y estados.
    Permite realizar seguimiento detallado de cada operación de caja.
    """

    # Campos visibles en la lista principal del admin
    list_display = ['id', 'pedido', 'monto_total', 'metodo_pago', 'estado', 'cajero', 'fecha_hora']

    # Filtros laterales para búsqueda rápida por estado, método de pago y fecha
    list_filter = ['estado', 'metodo_pago', 'fecha_hora']

    # Campos habilitados para búsqueda: factura, referencia y pedido
    search_fields = ['numero_factura', 'referencia', 'pedido__id']

    # Campos de solo lectura para preservar integridad de timestamps
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']

    # Navegación por jerarquía de fechas para análisis temporal
    date_hierarchy = 'fecha_hora'

    # Organización de campos en secciones para mejor usabilidad
    fieldsets = (
        ('Información del Pedido', {
            'fields': ('pedido', 'cajero')
        }),
        ('Datos de Pago', {
            'fields': ('monto_total', 'metodo_pago', 'estado', 'fecha_hora')
        }),
        ('Facturación', {
            'fields': ('numero_factura', 'comprobante_externo')
        }),
        ('Información Adicional', {
            'fields': ('referencia', 'observaciones')
        }),
        ('Timestamps', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DetallePago)
class DetallePagoAdmin(admin.ModelAdmin):
    """
    Administración de detalles de pago para transacciones divididas.

    Permite gestionar pagos que utilizan múltiples métodos (efectivo + tarjeta, etc.).
    Cada registro representa una forma de pago específica dentro de una transacción.
    """

    # Campos visibles: ID, transacción relacionada, método, monto y referencia
    list_display = ['id', 'transaccion', 'metodo_pago', 'monto', 'referencia']

    # Filtro por método de pago para análisis de uso de cada tipo
    list_filter = ['metodo_pago']

    # Búsqueda por referencia bancaria o número de factura de la transacción
    search_fields = ['referencia', 'transaccion__numero_factura']


@admin.register(CierreCaja)
class CierreCajaAdmin(admin.ModelAdmin):
    """
    Administración de cierres de caja por turno.

    Gestiona el proceso de arqueo de caja al finalizar cada turno.
    Registra totales por método de pago, calcula diferencias y mantiene
    el historial completo de operaciones financieras del día.
    """

    # Información principal: cajero, fecha, turno, totales y diferencias
    list_display = ['id', 'cajero', 'fecha', 'turno', 'total_ventas', 'diferencia', 'estado']

    # Filtros para analizar cierres por estado, turno y fecha
    list_filter = ['estado', 'turno', 'fecha']

    # Búsqueda por nombre o usuario del cajero responsable
    search_fields = ['cajero__username', 'cajero__first_name', 'cajero__last_name']

    # Campos calculados automáticamente que no deben modificarse
    readonly_fields = ['diferencia', 'hora_apertura', 'hora_cierre']

    # Navegación temporal para revisión de cierres históricos
    date_hierarchy = 'fecha'

    # Organización en secciones: turno, efectivo, métodos de pago, totales y horarios
    fieldsets = (
        ('Información del Turno', {
            'fields': ('cajero', 'fecha', 'turno', 'estado')
        }),
        ('Efectivo', {
            'fields': ('efectivo_inicial', 'efectivo_esperado', 'efectivo_real', 'diferencia')
        }),
        ('Ventas por Método', {
            'fields': ('total_efectivo', 'total_tarjeta', 'total_qr', 'total_movil')
        }),
        ('Totales', {
            'fields': ('total_ventas', 'total_descuentos', 'total_propinas', 'numero_pedidos')
        }),
        ('Horarios', {
            'fields': ('hora_apertura', 'hora_cierre')
        }),
        ('Observaciones', {
            'fields': ('observaciones',),
            'classes': ('collapse',)
        }),
    )


@admin.register(HistorialModificacion)
class HistorialModificacionAdmin(admin.ModelAdmin):
    """
    Administración del historial de modificaciones de pedidos.

    Mantiene una auditoría completa de todos los cambios realizados a los pedidos.
    Registra qué cambió, quién lo hizo, cuándo y por qué, garantizando trazabilidad
    total para resolución de conflictos y control de gestión.
    """

    # Campos principales: pedido, tipo de cambio, usuario responsable y fecha
    list_display = ['id', 'pedido', 'tipo_cambio', 'usuario', 'fecha_hora']

    # Filtros para analizar modificaciones por tipo y período temporal
    list_filter = ['tipo_cambio', 'fecha_hora']

    # Búsqueda por ID de pedido, usuario o motivo del cambio
    search_fields = ['pedido__id', 'usuario__username', 'motivo']

    # Timestamp inmutable para preservar integridad del registro
    readonly_fields = ['fecha_hora']

    # Jerarquía de fechas para análisis temporal de modificaciones
    date_hierarchy = 'fecha_hora'

    # Secciones: información general y detalles del cambio (antes/después)
    fieldsets = (
        ('Información General', {
            'fields': ('pedido', 'usuario', 'tipo_cambio', 'fecha_hora')
        }),
        ('Detalles del Cambio', {
            'fields': ('detalle_anterior', 'detalle_nuevo', 'motivo')
        }),
    )


@admin.register(AlertaStock)
class AlertaStockAdmin(admin.ModelAdmin):
    """
    Administración de alertas de stock de productos.

    Sistema de notificaciones para gestionar niveles críticos de inventario.
    Permite identificar productos con stock bajo o agotado, facilitando
    la reposición oportuna y evitando rupturas de servicio.
    """

    # Vista principal: producto, tipo de alerta, stock actual, estado y fecha
    list_display = ['id', 'producto', 'tipo_alerta', 'stock_actual', 'estado', 'fecha_creacion']

    # Filtros para priorizar alertas por tipo, estado y antigüedad
    list_filter = ['tipo_alerta', 'estado', 'fecha_creacion']

    # Búsqueda rápida por nombre de producto
    search_fields = ['producto__nombre']

    # Timestamps inmutables para trazabilidad de creación y resolución
    readonly_fields = ['fecha_creacion', 'fecha_resolucion']

    # Navegación temporal para análisis de patrones de agotamiento
    date_hierarchy = 'fecha_creacion'

    # Secciones: información de la alerta, proceso de resolución y timestamps
    fieldsets = (
        ('Información de la Alerta', {
            'fields': ('producto', 'tipo_alerta', 'estado', 'stock_actual')
        }),
        ('Resolución', {
            'fields': ('fecha_resolucion', 'resuelto_por', 'observaciones')
        }),
        ('Timestamps', {
            'fields': ('fecha_creacion',),
            'classes': ('collapse',)
        }),
    )
