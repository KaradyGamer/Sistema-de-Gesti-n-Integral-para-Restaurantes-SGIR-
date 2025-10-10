from rest_framework import serializers
from .models import Transaccion, DetallePago, CierreCaja, HistorialModificacion, AlertaStock
from app.pedidos.models import Pedido
from app.productos.models import Producto


class TransaccionSerializer(serializers.ModelSerializer):
    cajero_nombre = serializers.CharField(source='cajero.username', read_only=True)
    pedido_mesa = serializers.IntegerField(source='pedido.mesa.numero', read_only=True)

    class Meta:
        model = Transaccion
        fields = [
            'id', 'pedido', 'pedido_mesa', 'cajero', 'cajero_nombre',
            'monto_total', 'metodo_pago', 'estado', 'numero_factura',
            'comprobante_externo', 'referencia', 'observaciones',
            'fecha_hora', 'fecha_creacion'
        ]
        read_only_fields = ['id', 'fecha_creacion', 'numero_factura']


class DetallePagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetallePago
        fields = ['id', 'transaccion', 'metodo_pago', 'monto', 'referencia']
        read_only_fields = ['id']


class CierreCajaSerializer(serializers.ModelSerializer):
    cajero_nombre = serializers.CharField(source='cajero.username', read_only=True)

    class Meta:
        model = CierreCaja
        fields = [
            'id', 'cajero', 'cajero_nombre', 'fecha', 'turno', 'estado',
            'efectivo_inicial', 'total_efectivo', 'total_tarjeta',
            'total_qr', 'total_movil', 'total_ventas', 'efectivo_esperado',
            'efectivo_real', 'diferencia', 'total_descuentos', 'total_propinas',
            'numero_pedidos', 'observaciones', 'hora_apertura', 'hora_cierre'
        ]
        read_only_fields = [
            'id', 'diferencia', 'hora_apertura', 'hora_cierre',
            'total_efectivo', 'total_tarjeta', 'total_qr', 'total_movil',
            'total_ventas', 'efectivo_esperado', 'total_descuentos',
            'total_propinas', 'numero_pedidos'
        ]


class HistorialModificacionSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)
    tipo_cambio_display = serializers.CharField(source='get_tipo_cambio_display', read_only=True)

    class Meta:
        model = HistorialModificacion
        fields = [
            'id', 'pedido', 'usuario', 'usuario_nombre', 'tipo_cambio',
            'tipo_cambio_display', 'detalle_anterior', 'detalle_nuevo',
            'motivo', 'fecha_hora'
        ]
        read_only_fields = ['id', 'fecha_hora']


class AlertaStockSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    tipo_alerta_display = serializers.CharField(source='get_tipo_alerta_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    resuelto_por_nombre = serializers.CharField(source='resuelto_por.username', read_only=True, allow_null=True)

    class Meta:
        model = AlertaStock
        fields = [
            'id', 'producto', 'producto_nombre', 'tipo_alerta', 'tipo_alerta_display',
            'estado', 'estado_display', 'stock_actual', 'observaciones',
            'fecha_creacion', 'fecha_resolucion', 'resuelto_por', 'resuelto_por_nombre'
        ]
        read_only_fields = ['id', 'fecha_creacion', 'fecha_resolucion']