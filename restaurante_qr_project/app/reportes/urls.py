from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    # 📊 Dashboard principal
    path('dashboard/', views.dashboard_reportes, name='dashboard'),
    
    # 📈 APIs para gráficos
    path('api/ventas-semanales/', views.datos_ventas_semanales, name='api_ventas_semanales'),
    path('api/productos-top/', views.datos_productos_top, name='api_productos_top'),
    
    # 📄 Exportación (solo PDF/HTML)
    path('pdf/', views.generar_reporte_pdf, name='reporte_pdf'),
]