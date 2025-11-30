from django.contrib import admin
from .models import CategoriaInsumo, Insumo, MovimientoInsumo


@admin.register(CategoriaInsumo)
class CategoriaInsumoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo', 'fecha_creacion')
    list_filter = ('activo',)
    search_fields = ('nombre', 'descripcion')
    ordering = ('nombre',)


@admin.register(Insumo)
class InsumoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'stock_actual', 'stock_minimo', 'unidad', 'estado_stock', 'activo')
    list_filter = ('categoria', 'unidad', 'activo')
    search_fields = ('nombre', 'nota')
    ordering = ('nombre',)
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')

    def estado_stock(self, obj):
        if obj.agotado:
            return "🔴 AGOTADO"
        elif obj.stock_bajo:
            return "🟡 BAJO"
        else:
            return "🟢 OK"
    estado_stock.short_description = 'Estado'


@admin.register(MovimientoInsumo)
class MovimientoInsumoAdmin(admin.ModelAdmin):
    list_display = ('insumo', 'tipo', 'cantidad', 'fecha_creacion', 'creado_por')
    list_filter = ('tipo', 'fecha_creacion')
    search_fields = ('insumo__nombre', 'motivo')
    ordering = ('-fecha_creacion',)
    readonly_fields = ('fecha_creacion', 'creado_por')
