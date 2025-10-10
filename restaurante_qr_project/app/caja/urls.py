from django.urls import path
from . import views

app_name = 'caja'

urlpatterns = [
    # Panel principal
    path('', views.panel_caja, name='panel_caja'),

    # Pedidos y pagos
    path('pedido/<int:pedido_id>/', views.detalle_pedido, name='detalle_pedido'),
    path('pedido/<int:pedido_id>/pagar/', views.procesar_pago, name='procesar_pago'),
    path('pedido/<int:pedido_id>/modificar/', views.modificar_pedido, name='modificar_pedido'),
    path('pedido/<int:pedido_id>/reasignar/', views.reasignar_pedido, name='reasignar_pedido'),

    # Mapa de mesas
    path('mapa-mesas/', views.mapa_mesas, name='mapa_mesas'),

    # Historial
    path('historial/', views.historial_transacciones, name='historial'),

    # Caja (turnos)
    path('abrir/', views.abrir_caja, name='abrir_caja'),
    path('cerrar/', views.cierre_caja, name='cierre_caja'),

    # Alertas de stock
    path('alertas-stock/', views.alertas_stock_view, name='alertas_stock'),

    # 👥 MÓDULO DE PERSONAL (NUEVO)
    path('personal/', views.personal_panel, name='personal_panel'),
    path('personal/generar-qr/<int:empleado_id>/', views.generar_qr_empleado, name='generar_qr_empleado'),

    # 📅 GESTIÓN DE JORNADA LABORAL (NUEVO)
    path('jornada/', views.gestionar_jornada, name='gestionar_jornada'),
]