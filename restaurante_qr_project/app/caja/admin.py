from django.contrib import admin
from .models import Transaccion, DetallePago, CierreCaja, HistorialModificacion, AlertaStock


@admin.register(Transaccion)
class TransaccionAdmin(admin.ModelAdmin):
    list_display = ['id', 'pedido', 'monto_total', 'metodo_pago', 'estado', 'cajero', 'fecha_hora']
    list_filter = ['estado', 'metodo_pago', 'fecha_hora']
    search_fields = ['numero_factura', 'referencia', 'pedido__id']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    date_hierarchy = 'fecha_hora'

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
    list_display = ['id', 'transaccion', 'metodo_pago', 'monto', 'referencia']
    list_filter = ['metodo_pago']
    search_fields = ['referencia', 'transaccion__numero_factura']


@admin.register(CierreCaja)
class CierreCajaAdmin(admin.ModelAdmin):
    list_display = ['id', 'cajero', 'fecha', 'turno', 'total_ventas', 'diferencia', 'estado']
    list_filter = ['estado', 'turno', 'fecha']
    search_fields = ['cajero__username', 'cajero__first_name', 'cajero__last_name']
    readonly_fields = ['diferencia', 'hora_apertura', 'hora_cierre']
    date_hierarchy = 'fecha'

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
    list_display = ['id', 'pedido', 'tipo_cambio', 'usuario', 'fecha_hora']
    list_filter = ['tipo_cambio', 'fecha_hora']
    search_fields = ['pedido__id', 'usuario__username', 'motivo']
    readonly_fields = ['fecha_hora']
    date_hierarchy = 'fecha_hora'

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
    list_display = ['id', 'producto', 'tipo_alerta', 'stock_actual', 'estado', 'fecha_creacion']
    list_filter = ['tipo_alerta', 'estado', 'fecha_creacion']
    search_fields = ['producto__nombre']
    readonly_fields = ['fecha_creacion', 'fecha_resolucion']
    date_hierarchy = 'fecha_creacion'

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
