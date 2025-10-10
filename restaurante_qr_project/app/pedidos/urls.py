from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router para ViewSets
router = DefaultRouter()
router.register(r'pedidos', views.PedidoViewSet)

urlpatterns = [
    # 🔗 APIs ViewSet
    path('', include(router.urls)),
    
    # 👨🍳 APIs para Cocinero
    path('cocina/', views.pedidos_en_cocina_api, name='pedidos_cocina'),
    path('<int:pedido_id>/actualizar/', views.actualizar_estado_pedido, name='actualizar_estado'),
    
    # 🧾 APIs para Mesero (ORIGINALES)
    path('mesero/', views.pedidos_por_mesa, name='pedidos_mesero'),
    path('<int:pedido_id>/entregar/', views.marcar_entregado, name='marcar_entregado'),
    
    # 🆕 APIs para Panel Mesero Mejorado
    path('mesero/pedidos/', views.api_pedidos_mesero, name='api_pedidos_mesero'),
    path('mesero/reservas/', views.api_reservas_mesero, name='api_reservas_mesero'),
    path('mesero/entregar/<int:pedido_id>/', views.api_entregar_pedido, name='api_entregar_pedido'),
    path('mesero/confirmar-reserva/<int:reserva_id>/', views.api_confirmar_reserva, name='api_confirmar_reserva'),
    path('mesero/cambiar-estado-reserva/<int:reserva_id>/', views.api_cambiar_estado_reserva, name='api_cambiar_estado_reserva'),
    path('mesero/asignar-mesa/<int:reserva_id>/', views.api_asignar_mesa_reserva, name='api_asignar_mesa_reserva'),
    
    # 🛒 API Cliente
    path('cliente/crear/', views.crear_pedido_cliente, name='crear_pedido_cliente'),
]