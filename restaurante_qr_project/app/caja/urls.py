from django.urls import path
from . import views

app_name = 'caja'

urlpatterns = [
    # ============================================
    # PANEL UNIFICADO (TODO EN UNO)
    # ============================================
    path('', views.panel_unificado, name='panel_caja'),
    path('panel/', views.panel_unificado, name='panel_unificado'),

    # ============================================
    # GESTIÓN DE TURNOS
    # ============================================
    path('abrir/', views.abrir_caja, name='abrir_caja'),
    path('cerrar/', views.cierre_caja, name='cierre_caja'),

    # ============================================
    # GESTIÓN DE PERSONAL Y QR
    # ============================================
    path('personal/generar-qr/<int:empleado_id>/', views.generar_qr_empleado, name='generar_qr_empleado'),
]