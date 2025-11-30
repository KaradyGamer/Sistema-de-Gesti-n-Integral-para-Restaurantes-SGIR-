from django.urls import path
from . import views

app_name = 'inventario'

urlpatterns = [
    # Insumos
    path('insumos/', views.insumos_list, name='insumos'),
    path('insumos/nuevo/', views.insumos_crear, name='insumo_crear'),
    path('insumos/<int:pk>/editar/', views.insumos_editar, name='insumo_editar'),
    path('insumos/<int:pk>/eliminar/', views.insumos_eliminar, name='insumo_eliminar'),
    path('insumos/<int:pk>/ajustar/', views.insumos_ajustar_stock, name='insumo_ajustar'),

    # Categorías de insumos
    path('categorias/', views.categorias_insumo_list, name='categorias_insumo'),
    path('categorias/nuevo/', views.categorias_insumo_crear, name='categoria_insumo_crear'),
    path('categorias/<int:pk>/editar/', views.categorias_insumo_editar, name='categoria_insumo_editar'),
    path('categorias/<int:pk>/eliminar/', views.categorias_insumo_eliminar, name='categoria_insumo_eliminar'),

    # Movimientos
    path('movimientos/', views.movimientos_list, name='movimientos'),
]
