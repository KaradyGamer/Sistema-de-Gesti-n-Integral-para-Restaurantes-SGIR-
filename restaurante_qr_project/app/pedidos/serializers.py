# app/pedidos/serializers.py

from rest_framework import serializers
from .models import Pedido, DetallePedido
from app.productos.models import Producto
from app.productos.serializers import ProductoSerializer


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


class CrearPedidoSerializer(serializers.Serializer):
    """
    Serializer para crear pedidos (POST requests)
    No usa PedidoSerializer porque necesitamos escribir detalles
    """
    mesa_id = serializers.IntegerField()
    forma_pago = serializers.ChoiceField(
        choices=['efectivo', 'tarjeta', 'qr', 'movil', 'mixto'],
        default='efectivo'
    )
    observaciones = serializers.CharField(required=False, allow_blank=True)
    productos = serializers.ListField(
        child=serializers.DictField(child=serializers.IntegerField()),
        min_length=1,
        help_text='Lista de productos: [{"producto_id": 1, "cantidad": 2}, ...]'
    )

    def validate_productos(self, value):
        """Validar que cada producto tenga los campos necesarios"""
        for item in value:
            if 'producto_id' not in item and 'producto' not in item and 'id' not in item:
                raise serializers.ValidationError('Cada producto debe tener "producto_id", "producto" o "id"')
            if 'cantidad' not in item:
                raise serializers.ValidationError('Cada producto debe tener "cantidad"')
            if item['cantidad'] <= 0:
                raise serializers.ValidationError('La cantidad debe ser mayor a 0')
        return value

    def create(self, validated_data):
        """Crear pedido con sus detalles"""
        from app.mesas.models import Mesa
        from django.utils import timezone

        mesa_id = validated_data['mesa_id']
        productos_data = validated_data['productos']
        forma_pago = validated_data.get('forma_pago', 'efectivo')
        observaciones = validated_data.get('observaciones', '')

        # Buscar mesa
        try:
            mesa = Mesa.objects.get(id=mesa_id)
        except Mesa.DoesNotExist:
            try:
                # Fallback: buscar por número
                mesa = Mesa.objects.get(numero=mesa_id)
            except Mesa.DoesNotExist:
                raise serializers.ValidationError({'mesa_id': f'Mesa {mesa_id} no encontrada'})

        # Crear pedido
        pedido = Pedido.objects.create(
            mesa=mesa,
            fecha=timezone.now(),
            forma_pago=forma_pago,
            observaciones=observaciones,
            estado='pendiente'
        )

        # Crear detalles
        total = 0
        for item in productos_data:
            # Obtener producto_id con múltiples nombres posibles
            producto_id = item.get('producto_id') or item.get('producto') or item.get('id')
            cantidad = item['cantidad']

            try:
                producto = Producto.objects.get(id=producto_id, disponible=True)
            except Producto.DoesNotExist:
                pedido.delete()  # Limpiar pedido si falla
                raise serializers.ValidationError({
                    'productos': f'Producto ID {producto_id} no encontrado o no disponible'
                })

            subtotal = producto.precio * cantidad
            total += subtotal

            DetallePedido.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=cantidad,
                subtotal=subtotal
            )

            # Descontar stock si el producto lo requiere
            if producto.requiere_inventario:
                if not producto.descontar_stock(cantidad):
                    pedido.delete()
                    raise serializers.ValidationError({
                        'productos': f'Stock insuficiente para {producto.nombre}'
                    })

        # Actualizar total del pedido
        pedido.total = total
        pedido.total_final = total
        pedido.save()

        return pedido
