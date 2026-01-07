from django.urls import path
from . import views, api_views

app_name = 'reportes'

urlpatterns = [
    # 📊 Dashboard principal
    path('dashboard/', views.dashboard_reportes, name='dashboard'),

    # 📈 APIs para gráficos
    path('api/ventas-semanales/', views.datos_ventas_semanales, name='api_ventas_semanales'),
    path('api/productos-top/', views.datos_productos_top, name='api_productos_top'),

    # 📄 Exportación (solo PDF/HTML)
    path('pdf/', views.generar_reporte_pdf, name='reporte_pdf'),

    # ═══════════════════════════════════════════
    # RONDA 4: EXPORTACIÓN DE REPORTES PDF/EXCEL
    # ═══════════════════════════════════════════

    # 📊 Reporte de Ventas
    path('exportar/ventas/xlsx/', api_views.ventas_xlsx, name='ventas_xlsx'),
    path('exportar/ventas/pdf/', api_views.ventas_pdf, name='ventas_pdf'),

    # 💰 Reporte de Caja (Turnos)
    path('exportar/caja/xlsx/', api_views.caja_xlsx, name='caja_xlsx'),
    path('exportar/caja/pdf/', api_views.caja_pdf, name='caja_pdf'),

    # 💸 Reporte de Reembolsos
    path('exportar/reembolsos/xlsx/', api_views.reembolsos_xlsx, name='reembolsos_xlsx'),
    path('exportar/reembolsos/pdf/', api_views.reembolsos_pdf, name='reembolsos_pdf'),

    # 🏆 Top Productos Más Vendidos
    path('exportar/top-productos/xlsx/', api_views.top_productos_xlsx, name='top_productos_xlsx'),
    path('exportar/top-productos/pdf/', api_views.top_productos_pdf, name='top_productos_pdf'),
]