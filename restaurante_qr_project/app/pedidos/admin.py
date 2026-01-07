# app/pedidos/admin.py - RONDA 2 HARDENING: Validación de transiciones en Admin
from django.contrib import admin
from django.core.exceptions import ValidationError

# Si tienes los modelos definidos, usa esta versión:
try:
    from .models import Pedido, DetallePedido
    from app.pedidos.utils import validar_transicion_estado

    @admin.register(Pedido)
    class PedidoAdmin(admin.ModelAdmin):
        list_display = ['id', 'mesa', 'estado', 'total', 'fecha']
        list_filter = ['estado', 'fecha']
        search_fields = ['id', 'mesa__numero']

        def save_model(self, request, obj, form, change):
            """
            ✅ RONDA 2 HARDENING: Validar transiciones de estado en Admin
            Previene bypass de la máquina de estados desde Django Admin
            """
            if change and 'estado' in form.changed_data:
                # Obtener estado original desde la base de datos
                original = Pedido.objects.get(pk=obj.pk)
                try:
                    # Validar transición usando la función central
                    validar_transicion_estado(original.estado, obj.estado)
                except ValueError as e:
                    # Convertir ValueError a ValidationError para que Django lo maneje
                    raise ValidationError({
                        'estado': str(e)
                    })

            super().save_model(request, obj, form, change)

    @admin.register(DetallePedido)
    class DetallePedidoAdmin(admin.ModelAdmin):
        list_display = ['pedido', 'producto', 'cantidad', 'subtotal']
        list_filter = ['producto']

except ImportError:
    # Si no existen los modelos, importar solo lo que existe
    try:
        from .models import Pedido
        from app.pedidos.utils import validar_transicion_estado

        @admin.register(Pedido)
        class PedidoAdmin(admin.ModelAdmin):
            list_display = ['id', 'mesa', 'estado', 'total', 'fecha']
            list_filter = ['estado', 'fecha']
            search_fields = ['id']

            def save_model(self, request, obj, form, change):
                if change and 'estado' in form.changed_data:
                    original = Pedido.objects.get(pk=obj.pk)
                    try:
                        validar_transicion_estado(original.estado, obj.estado)
                    except ValueError as e:
                        raise ValidationError({'estado': str(e)})
                super().save_model(request, obj, form, change)
    except ImportError:
        # Si no existe ningún modelo, dejar vacío
        pass