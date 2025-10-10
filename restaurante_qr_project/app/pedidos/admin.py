# app/pedidos/admin.py - SOLUCIÓN RÁPIDA
from django.contrib import admin

# Comentar temporalmente las importaciones problemáticas
# from .models import Pedido, DetallePedido

# Si tienes los modelos definidos, usa esta versión:
try:
    from .models import Pedido, DetallePedido
    
    @admin.register(Pedido)
    class PedidoAdmin(admin.ModelAdmin):
        list_display = ['id', 'mesa', 'estado', 'total', 'fecha']
        list_filter = ['estado', 'fecha']
        search_fields = ['id', 'mesa__numero']
    
    @admin.register(DetallePedido)
    class DetallePedidoAdmin(admin.ModelAdmin):
        list_display = ['pedido', 'producto', 'cantidad', 'subtotal']
        list_filter = ['producto']

except ImportError:
    # Si no existen los modelos, importar solo lo que existe
    try:
        from .models import Pedido
        
        @admin.register(Pedido)
        class PedidoAdmin(admin.ModelAdmin):
            list_display = ['id', 'mesa', 'estado', 'total', 'fecha']
            list_filter = ['estado', 'fecha']
            search_fields = ['id']
    except ImportError:
        # Si no existe ningún modelo, dejar vacío
        pass