# app/productos/urls.py - CREAR O REEMPLAZAR
from django.urls import path
from . import views

urlpatterns = [
    # API para el menú del cliente
    path('agrupados/', views.productos_agrupados, name='productos_agrupados'),
    path('', views.lista_productos, name='lista_productos'),
]