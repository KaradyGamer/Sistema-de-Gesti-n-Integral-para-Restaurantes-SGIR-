from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView, RedirectView

# ✅ IMPORTACIONES BÁSICAS CORREGIDAS
from app.pedidos.views import (
    formulario_cliente,
    vista_exito,
    confirmacion_pedido,
    panel_cocina,
    panel_mesero,
    pedidos_por_mesa,
    pedidos_en_cocina_api,
    actualizar_estado_pedido,
    marcar_entregado,
    crear_pedido_cliente,
)
from rest_framework_simplejwt.views import TokenRefreshView
from app.usuarios.views_empleado import panel_empleado
from app.usuarios.views import qr_login  # ✅ NUEVO: Para login por QR

urlpatterns = [
    path('admin/', admin.site.urls),

    # 🔐 SISTEMA DE LOGIN
    path('login/', TemplateView.as_view(template_name='login.html'), name='login'),
    path('qr-login/<uuid:token>/', qr_login, name='qr_login'),  # ✅ NUEVO: Login por QR desde raíz

    # 🎨 FAVICON (evita error 404)
    path('favicon.ico', RedirectView.as_view(url='/static/admin/img/icon-yes.svg', permanent=True)),

    # 🌍 CAMBIO DE IDIOMA (para admin_interface - opcional)
    path('i18n/', include('django.conf.urls.i18n')),

    # 🍽️ SISTEMA DE RESERVAS
    path('reservas/', include('app.reservas.urls')), 
    
    # ✅ SISTEMA DE REPORTES (NAMESPACE ÚNICO)
    path('reportes/', include(('app.reportes.urls', 'reportes'), namespace='reportes_web')), 
    
    # ✅ RUTAS BÁSICAS DEL SISTEMA
    path('', formulario_cliente, name='formulario_cliente'),
    path('menu/', formulario_cliente, name='menu_cliente'),  # Apunta a formulario_cliente (mismo template)
    path('confirmacion/', confirmacion_pedido, name='confirmacion_pedido'),
    path('exito/', vista_exito, name='vista_exito'),
    path('cocina/', panel_cocina, name='panel_cocina'),
    path('mesero/', panel_mesero, name='panel_mesero'),
    
    # ✅ AUTENTICACIÓN JWT
    path('api/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # ✅ APIs PRINCIPALES (CORREGIDAS)
    path('api/pedidos/cocina/', pedidos_en_cocina_api, name='pedidos_cocina'),  # ✅ CAMBIADO: PedidosEnCocinaAPIView.as_view() → pedidos_en_cocina_api
    path('api/pedidos/mesero/', pedidos_por_mesa, name='pedidos_mesero'),
    path('api/pedidos/<int:pedido_id>/actualizar/', actualizar_estado_pedido, name='actualizar_estado'),
    path('api/pedidos/<int:pedido_id>/entregar/', marcar_entregado, name='marcar_entregado'),
    path('api/pedidos/cliente/crear/', crear_pedido_cliente, name='crear_pedido_cliente'),
    
    # ✅ INCLUDES DE APPS
    path('usuarios/', include('app.usuarios.urls')),  # ✅ Para /usuarios/session-login/
    path('api/usuarios/', include(('app.usuarios.urls', 'usuarios'), namespace='api_usuarios')),  # ✅ SOLUCIONADO: Namespace único
    path('api/productos/', include('app.productos.urls')),
    path('api/mesas/', include('app.mesas.urls')),
    path('api/pedidos/', include('app.pedidos.urls')),  # ✅ ESTO HACE QUE LAS URLs SEAN /api/pedidos/mesero/reservas/
    path('api/reportes/', include(('app.reportes.urls', 'reportes'), namespace='reportes_api')),  # ✅ NAMESPACE ÚNICO
    path('api/reservas/', include('app.reservas.urls')),

    # 💰 MÓDULO DE CAJA
    path('caja/', include('app.caja.urls')),  # Vistas HTML del cajero
    path('api/caja/', include('app.caja.api_urls')),  # APIs REST del cajero

    # 👥 PANEL UNIFICADO DE EMPLEADOS (Ya importado arriba)
    path('empleado/', panel_empleado, name='panel_empleado'),

    # 🎨 ADMINUX - Panel de administración moderno
    path('adminux/', include('app.adminux.urls')),
]

# ✅ ARCHIVOS ESTÁTICOS Y MEDIA
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)