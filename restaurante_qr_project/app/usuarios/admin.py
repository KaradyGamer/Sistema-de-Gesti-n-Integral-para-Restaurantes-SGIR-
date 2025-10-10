from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import Usuario, AREAS_SISTEMA

class UsuarioAdmin(UserAdmin):
    model = Usuario
    list_display = ['username', 'nombre_completo', 'rol', 'pin', 'estado_activo', 'areas_display', 'is_staff']
    list_filter = ['rol', 'activo', 'is_staff', 'is_superuser']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'pin']

    def nombre_completo(self, obj):
        return obj.get_full_name() or obj.username
    nombre_completo.short_description = 'Nombre'

    def estado_activo(self, obj):
        if obj.activo:
            return format_html('<span style="color: green;">✓ Activo</span>')
        return format_html('<span style="color: red;">✗ Inactivo</span>')
    estado_activo.short_description = 'Estado'

    def areas_display(self, obj):
        areas = obj.get_areas_activas()
        if not areas:
            return '-'
        return ', '.join(areas)
    areas_display.short_description = 'Áreas Permitidas'

    # Campos visibles al editar un usuario
    fieldsets = UserAdmin.fieldsets + (
        ('Información del Empleado', {
            'fields': ('rol', 'activo')
        }),
        ('Acceso y Seguridad', {
            'fields': ('pin', 'qr_token', 'fecha_ultimo_qr'),
            'description': 'PIN para acceso rápido. El QR token se genera automáticamente.'
        }),
        ('Permisos Multi-Área', {
            'fields': ('areas_permitidas',),
            'description': 'Selecciona las áreas a las que el usuario tiene acceso. Deja vacío para usar permisos por defecto según su rol.'
        }),
    )

    # Campos visibles al crear un nuevo usuario
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información del Empleado', {
            'fields': ('rol', 'first_name', 'last_name', 'email', 'activo')
        }),
        ('Acceso Rápido (Opcional)', {
            'fields': ('pin',),
            'description': 'PIN de 4-6 dígitos para acceso rápido (solo números)'
        }),
        ('Permisos Multi-Área (Opcional)', {
            'fields': ('areas_permitidas',),
            'description': 'Áreas disponibles: mesero, cocina, caja, reportes'
        }),
    )

    readonly_fields = ['qr_token', 'fecha_ultimo_qr']

admin.site.register(Usuario, UsuarioAdmin)
