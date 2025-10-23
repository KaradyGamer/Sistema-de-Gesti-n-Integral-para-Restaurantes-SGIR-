# app/pedidos/serializers.py

from rest_framework import serializers
from .models import Pedido, DetallePedido
from app.productos.models import Producto


class DetallePedidoSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    producto_precio = serializers.DecimalField(source='producto.precio', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = DetallePedido
        fields = ['id', 'producto', 'producto_nombre', 'producto_precio', 'cantidad', 'subtotal']
        read_only_fields = ['id', 'producto_nombre', 'producto_precio', 'subtotal']


class PedidoSerializer(serializers.ModelSerializer):
    """
    Serializer para lectura de pedidos (GET requests)
    """
    detalles = DetallePedidoSerializer(many=True, read_only=True)
    mesa_numero = serializers.IntegerField(source='mesa.numero', read_only=True)
    modificado_por = serializers.SerializerMethodField()

    class Meta:
        model = Pedido
        fields = ['id', 'mesa', 'mesa_numero', 'fecha', 'estado', 'estado_pago', 'total', 'total_final', 'detalles', 'modificado', 'modificado_por']
        read_only_fields = ['id', 'fecha', 'total', 'total_final', 'modificado', 'modificado_por']

    def get_modificado_por(self, obj):
        """Obtiene el nombre del último usuario que modificó el pedido"""
        if not obj.modificado:
            return None

        # Buscar la última modificación
        ultima_modificacion = obj.historial_modificaciones.order_by('-fecha_hora').first()
        if ultima_modificacion and ultima_modificacion.usuario:
            return {
                'nombre': ultima_modificacion.usuario.get_full_name() or ultima_modificacion.usuario.username,
                'username': ultima_modificacion.usuario.username,
                'fecha': ultima_modificacion.fecha_hora
            }
        return None
