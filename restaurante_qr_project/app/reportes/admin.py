from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import ReporteVentas

@admin.register(ReporteVentas)
class ReporteVentasAdmin(admin.ModelAdmin):
    list_display = [
        'tipo', 
        'fecha_inicio', 
        'fecha_fin', 
        'total_ventas_formatted', 
        'total_pedidos', 
        'promedio_por_pedido_formatted',
        'producto_mas_vendido_short',
        'fecha_generacion',
        'acciones_reporte'
    ]
    
    list_filter = ['tipo', 'fecha_generacion', 'fecha_inicio']
    search_fields = ['producto_mas_vendido', 'observaciones']
    ordering = ['-fecha_generacion']
    readonly_fields = [
        'total_ventas', 
        'total_pedidos', 
        'promedio_por_pedido',
        'producto_mas_vendido',
        'dia_mas_ventas',
        'observaciones',
        'fecha_generacion'
    ]
    
    fieldsets = (
        ('Información del Reporte', {
            'fields': ('tipo', 'fecha_inicio', 'fecha_fin')
        }),
        ('Estadísticas', {
            'fields': (
                'total_ventas', 
                'total_pedidos', 
                'promedio_por_pedido',
                'producto_mas_vendido',
                'dia_mas_ventas'
            )
        }),
        ('Análisis', {
            'fields': ('observaciones',),
            'classes': ('wide',)
        }),
        ('Metadatos', {
            'fields': ('fecha_generacion',),
            'classes': ('collapse',)
        })
    )
    
    def total_ventas_formatted(self, obj):
        return f"S/. {obj.total_ventas:,.2f}"
    total_ventas_formatted.short_description = "Total Ventas"
    total_ventas_formatted.admin_order_field = "total_ventas"
    
    def promedio_por_pedido_formatted(self, obj):
        return f"S/. {obj.promedio_por_pedido:,.2f}"
    promedio_por_pedido_formatted.short_description = "Promedio/Pedido"
    promedio_por_pedido_formatted.admin_order_field = "promedio_por_pedido"
    
    def producto_mas_vendido_short(self, obj):
        if len(obj.producto_mas_vendido) > 30:
            return f"{obj.producto_mas_vendido[:30]}..."
        return obj.producto_mas_vendido
    producto_mas_vendido_short.short_description = "Producto Top"
    
    def acciones_reporte(self, obj):
        try:
            dashboard_url = '/reportes/dashboard/'
            csv_url = reverse('reportes:reporte_csv')
            pdf_url = reverse('reportes:reporte_pdf')
            
            return format_html(
                '<a href="{}" style="background: #007bff; color: white; padding: 5px 10px; '
                'text-decoration: none; border-radius: 3px; margin-right: 5px;" target="_blank">📊 Dashboard</a>'
                '<a href="{}" style="background: #28a745; color: white; padding: 5px 10px; '
                'text-decoration: none; border-radius: 3px; margin-right: 5px;">📊 CSV</a>'
                '<a href="{}" style="background: #dc3545; color: white; padding: 5px 10px; '
                'text-decoration: none; border-radius: 3px;" target="_blank">📄 Reporte</a>',
                dashboard_url, csv_url, pdf_url
            )
        except Exception as e:
            return format_html(
                '<a href="/reportes/dashboard/" style="background: #007bff; color: white; padding: 5px 10px; '
                'text-decoration: none; border-radius: 3px;" target="_blank">📊 Dashboard</a>'
            )
    acciones_reporte.short_description = "Acciones"
    acciones_reporte.allow_tags = True
    
    def changelist_view(self, request, extra_context=None):
        # Agregar botón personalizado en la lista
        extra_context = extra_context or {}
        extra_context['dashboard_url'] = '/reportes/dashboard/'
        return super().changelist_view(request, extra_context)
    
    def has_add_permission(self, request):
        # Los reportes se generan automáticamente
        return False