from django.contrib import admin
from .models import ConfiguracionSistema


@admin.register(ConfiguracionSistema)
class ConfiguracionSistemaAdmin(admin.ModelAdmin):
    """Admin para configuración del sistema (singleton)"""

    list_display = ('nombre', 'nit', 'moneda', 'tema', 'fecha_actualizacion')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')

    fieldsets = (
        ('Información del Negocio', {
            'fields': ('nombre', 'nit', 'direccion', 'telefono', 'email', 'logo', 'lema')
        }),
        ('Configuración Financiera', {
            'fields': ('moneda', 'impuesto', 'propina_sugerida')
        }),
        ('Sistema', {
            'fields': ('idioma', 'zona_horaria', 'tema')
        }),
        ('Horarios', {
            'fields': ('hora_apertura', 'hora_cierre')
        }),
        ('Reservas', {
            'fields': ('reserva_max_minutos', 'reserva_tolerancia_minutos')
        }),
        ('Tickets', {
            'fields': ('ticket_footer',)
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        """Solo permitir crear si no existe ningún registro"""
        return not ConfiguracionSistema.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """No permitir borrar configuración"""
        return False
