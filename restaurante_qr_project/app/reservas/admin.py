from django.contrib import admin
from .models import Reserva

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = [
        'nombre_completo', 'numero_carnet', 'fecha_reserva', 
        'hora_reserva', 'numero_personas', 'estado', 'mesa'
    ]
    list_filter = ['estado', 'fecha_reserva', 'numero_personas']
    search_fields = ['nombre_completo', 'numero_carnet', 'telefono']
    list_editable = ['estado']
    date_hierarchy = 'fecha_reserva'
    ordering = ['-fecha_reserva', '-hora_reserva']
    
    fieldsets = (
        ('Información del Cliente', {
            'fields': ('numero_carnet', 'nombre_completo', 'telefono', 'email')
        }),
        ('Detalles de la Reserva', {
            'fields': ('fecha_reserva', 'hora_reserva', 'numero_personas', 'mesa')
        }),
        ('Estado y Observaciones', {
            'fields': ('estado', 'observaciones')
        }),
    )