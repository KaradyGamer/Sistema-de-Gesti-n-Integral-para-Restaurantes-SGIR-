"""
SGIR v40.5.1 - URLs del módulo Producción
"""
from django.urls import path
from . import views

app_name = 'produccion'

urlpatterns = [
    # Recetas
    path('recetas/', views.api_recetas, name='api_recetas'),
    path('recetas/<int:producto_id>/', views.api_actualizar_receta, name='api_actualizar_receta'),

    # Producción
    path('registrar/', views.api_registrar_produccion, name='api_registrar_produccion'),
    path('aplicar/<int:produccion_id>/', views.api_aplicar_produccion, name='api_aplicar_produccion'),
    path('anular/<int:produccion_id>/', views.api_anular_produccion, name='api_anular_produccion'),
    path('listado/', views.api_listado_producciones, name='api_listado_producciones'),
]