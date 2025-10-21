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

    class Meta:
        model = Pedido
        fields = ['id', 'mesa', 'mesa_numero', 'fecha', 'estado', 'estado_pago', 'total', 'total_final', 'detalles']
        read_only_fields = ['id', 'fecha', 'total', 'total_final']
