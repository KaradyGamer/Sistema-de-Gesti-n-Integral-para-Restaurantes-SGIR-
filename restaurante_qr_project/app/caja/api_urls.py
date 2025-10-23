from django.urls import path
from . import api_views

app_name = 'caja_api'

urlpatterns = [
    # ═══════════════════════════════════════════
    # CONSULTAS DE PEDIDOS
    # ═══════════════════════════════════════════
    path('pedidos/pendientes/', api_views.api_pedidos_pendientes_pago, name='pedidos_pendientes'),
    path('pedidos/kanban/', api_views.api_pedidos_kanban, name='pedidos_kanban'),
    path('pedidos/<int:pedido_id>/cambiar-estado/', api_views.api_cambiar_estado_pedido, name='cambiar_estado'),
    path('pedidos/<int:pedido_id>/', api_views.api_detalle_pedido, name='detalle_pedido'),
    path('pedidos/<int:pedido_id>/historial/', api_views.api_historial_modificaciones, name='historial_modificaciones'),

    # ═══════════════════════════════════════════
    # PROCESAMIENTO DE PAGOS
    # ═══════════════════════════════════════════
    path('pago/simple/', api_views.api_procesar_pago_simple, name='procesar_pago_simple'),
    path('pago/mixto/', api_views.api_procesar_pago_mixto, name='procesar_pago_mixto'),

    # ═══════════════════════════════════════════
    # MODIFICACIÓN DE PEDIDOS
    # ═══════════════════════════════════════════
    path('pedidos/descuento/', api_views.api_aplicar_descuento, name='aplicar_descuento'),
    path('pedidos/propina/', api_views.api_aplicar_propina, name='aplicar_propina'),
    path('pedidos/agregar-producto/', api_views.api_agregar_producto_pedido, name='agregar_producto'),
    path('pedidos/detalle/<int:detalle_id>/eliminar/', api_views.api_eliminar_producto_pedido, name='eliminar_producto'),
    path('pedidos/detalle/<int:detalle_id>/cantidad/', api_views.api_modificar_cantidad_producto, name='modificar_cantidad'),
    path('pedidos/reasignar-mesa/', api_views.api_reasignar_pedido_mesa, name='reasignar_mesa'),

    # ═══════════════════════════════════════════
    # GESTIÓN DE CAJA (TURNOS)
    # ═══════════════════════════════════════════
    path('turno/abrir/', api_views.api_abrir_caja, name='abrir_turno'),
    path('turno/cerrar/', api_views.api_cerrar_caja, name='cerrar_turno'),

    # ═══════════════════════════════════════════
    # CONSULTAS GENERALES
    # ═══════════════════════════════════════════
    path('mapa-mesas/', api_views.api_mapa_mesas, name='mapa_mesas'),
    path('estadisticas/', api_views.api_estadisticas_dia, name='estadisticas'),
    path('alertas-stock/', api_views.api_alertas_stock, name='alertas_stock'),
    path('alertas-stock/<int:alerta_id>/resolver/', api_views.api_resolver_alerta_stock, name='resolver_alerta'),

    # ═══════════════════════════════════════════
    # GESTIÓN DE PERSONAL
    # ═══════════════════════════════════════════
    path('empleados/', api_views.api_lista_empleados, name='lista_empleados'),
]