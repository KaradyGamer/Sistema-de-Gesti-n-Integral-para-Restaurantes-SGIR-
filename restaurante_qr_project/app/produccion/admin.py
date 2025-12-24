"""
SGIR v40.5.0 - Admin de Producción
"""
from django.contrib import admin
from .models import Receta, RecetaItem, Produccion, ProduccionDetalle


class RecetaItemInline(admin.TabularInline):
    model = RecetaItem
    extra = 1
    fields = ['insumo', 'cantidad', 'merma_pct']


@admin.register(Receta)
class RecetaAdmin(admin.ModelAdmin):
    list_display = ['producto', 'version', 'activo', 'fecha_creacion']
    list_filter = ['activo', 'fecha_creacion']
    search_fields = ['producto__nombre']
    inlines = [RecetaItemInline]
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']


class ProduccionDetalleInline(admin.TabularInline):
    model = ProduccionDetalle
    extra = 0
    fields = ['insumo', 'cantidad_calculada', 'unidad_snapshot', 'stock_insumo_antes', 'stock_insumo_despues']
    readonly_fields = ['insumo', 'cantidad_calculada', 'unidad_snapshot', 'stock_insumo_antes', 'stock_insumo_despues']
    can_delete = False


@admin.register(Produccion)
class ProduccionAdmin(admin.ModelAdmin):
    list_display = ['id', 'producto', 'cantidad_producida', 'lote', 'estado', 'creado_por', 'fecha_creacion']
    list_filter = ['estado', 'fecha_creacion', 'producto']
    search_fields = ['producto__nombre', 'lote']
    readonly_fields = [
        'receta', 'creado_por', 'fecha_creacion',
        'aplicado_por', 'fecha_aplicacion',
        'anulado_por', 'fecha_anulacion', 'motivo_anulacion',
        'pin_secundario_validado'
    ]
    inlines = [ProduccionDetalleInline]
    fieldsets = (
        ('Información General', {
            'fields': ('producto', 'receta', 'cantidad_producida', 'lote', 'estado', 'notas')
        }),
        ('Auditoría de Creación', {
            'fields': ('creado_por', 'fecha_creacion')
        }),
        ('Auditoría de Aplicación', {
            'fields': ('aplicado_por', 'fecha_aplicacion'),
            'classes': ('collapse',)
        }),
        ('Auditoría de Anulación', {
            'fields': ('anulado_por', 'fecha_anulacion', 'motivo_anulacion', 'pin_secundario_validado'),
            'classes': ('collapse',)
        }),
    )

    def has_delete_permission(self, request, obj=None):
        # No permitir borrar producciones desde admin
        return False