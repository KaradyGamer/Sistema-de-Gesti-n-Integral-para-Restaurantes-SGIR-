from django.urls import path
from . import views

urlpatterns = [
    # 🍽️ VISTAS PRINCIPALES DEL SISTEMA DE RESERVAS
    path('', views.reservar_mesa, name='reservar_mesa'),
    path('consultar/', views.consultar_reserva, name='consultar_reserva'),
    path('editar/<int:reserva_id>/', views.editar_reserva, name='editar_reserva'),  # 🆕 NUEVA FUNCIONALIDAD
    path('confirmacion/<int:reserva_id>/', views.confirmacion_reserva, name='confirmacion_reserva'),
    path('panel/', views.panel_reservas, name='panel_reservas'),
    
    # 🔌 APIs REST PARA EL SISTEMA DE RESERVAS
    path('api/mesas-disponibles/', views.mesas_disponibles, name='mesas_disponibles'),
    path('api/cancelar/<int:reserva_id>/', views.cancelar_reserva, name='cancelar_reserva'),  # 🆕 NUEVA API
    path('api/cambiar-estado/<int:reserva_id>/', views.cambiar_estado_reserva, name='cambiar_estado_reserva'),
]