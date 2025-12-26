from django.urls import path
from . import views

app_name = 'integraciones'

urlpatterns = [
    path('health/', views.health_check, name='health'),
    path('inventario/stock-bajo/', views.inventario_stock_bajo, name='inventario_stock_bajo'),
    path('caja/resumen-cierres/', views.caja_resumen_cierres, name='caja_resumen_cierres'),
]
