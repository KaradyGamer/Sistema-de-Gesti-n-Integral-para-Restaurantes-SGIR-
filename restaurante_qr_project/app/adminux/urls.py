from django.urls import path
from . import views

app_name = 'adminux'

urlpatterns = [
    # Dashboard principal
    path('', views.dashboard, name='dashboard'),

    # ══════════════════════════════════════════
    # GESTIÓN DE USUARIOS
    # ══════════════════════════════════════════
    path('usuarios/', views.usuarios_list, name='usuarios'),
    path('usuarios/crear/', views.usuarios_crear, name='usuario_crear'),
    path('usuarios/<int:pk>/editar/', views.usuarios_editar, name='usuario_editar'),
    path('usuarios/<int:pk>/eliminar/', views.usuarios_eliminar, name='usuario_eliminar'),

    # ══════════════════════════════════════════
    # GESTIÓN DE PRODUCTOS
    # ══════════════════════════════════════════
    path('productos/', views.productos_list, name='productos'),
    path('productos/crear/', views.productos_crear, name='producto_crear'),
    path('productos/<int:pk>/editar/', views.productos_editar, name='producto_editar'),
    path('productos/<int:pk>/eliminar/', views.productos_eliminar, name='producto_eliminar'),

    # ══════════════════════════════════════════
    # GESTIÓN DE CATEGORÍAS
    # ══════════════════════════════════════════
    path('categorias/', views.categorias_list, name='categorias'),
    path('categorias/crear/', views.categorias_crear, name='categoria_crear'),
    path('categorias/<int:pk>/editar/', views.categorias_editar, name='categoria_editar'),
    path('categorias/<int:pk>/eliminar/', views.categorias_eliminar, name='categoria_eliminar'),

    # ══════════════════════════════════════════
    # GESTIÓN DE MESAS
    # ══════════════════════════════════════════
    path('mesas/', views.mesas_list, name='mesas'),
    path('mesas/crear/', views.mesas_crear, name='mesa_crear'),
    path('mesas/<int:pk>/editar/', views.mesas_editar, name='mesa_editar'),
    path('mesas/<int:pk>/eliminar/', views.mesas_eliminar, name='mesa_eliminar'),

    # ══════════════════════════════════════════
    # GESTIÓN DE PEDIDOS
    # ══════════════════════════════════════════
    path('pedidos/', views.pedidos_list, name='pedidos'),
    path('pedidos/<int:pk>/', views.pedidos_detalle, name='pedido_detalle'),

    # ══════════════════════════════════════════
    # GESTIÓN DE RESERVAS
    # ══════════════════════════════════════════
    path('reservas/', views.reservas_list, name='reservas'),
    path('reservas/crear/', views.reservas_crear, name='reserva_crear'),
    path('reservas/<int:pk>/editar/', views.reservas_editar, name='reserva_editar'),
    path('reservas/<int:pk>/eliminar/', views.reservas_eliminar, name='reserva_eliminar'),

    # ══════════════════════════════════════════
    # REPORTES Y ESTADÍSTICAS
    # ══════════════════════════════════════════
    path('reportes/', views.reportes, name='reportes'),
    path('reportes/ventas/', views.reportes_ventas, name='reportes_ventas'),
    path('reportes/productos/', views.reportes_productos, name='reportes_productos'),

    # ══════════════════════════════════════════
    # CONFIGURACIÓN DEL SISTEMA
    # ══════════════════════════════════════════
    path('configuracion/', views.configuracion, name='configuracion'),
]
