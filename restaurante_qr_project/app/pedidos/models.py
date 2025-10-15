from django.db import models
from django.utils import timezone

class Pedido(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en preparacion', 'En Preparación'),
        ('listo', 'Listo'),
        ('entregado', 'Entregado'),
    ]

    FORMA_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('qr', 'Código QR'),
        ('movil', 'Pago Móvil'),  # Nuevo método de pago
        ('mixto', 'Pago Mixto'),  # Para pagos combinados
    ]

    ESTADO_PAGO_CHOICES = [
        ('pendiente', 'Pendiente de Pago'),
        ('parcial', 'Pago Parcial'),
        ('pagado', 'Pagado Completo'),
        ('cancelado', 'Cancelado'),
    ]

    # Campos existentes
    mesa = models.ForeignKey('mesas.Mesa', on_delete=models.PROTECT, related_name='pedidos')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fecha = models.DateTimeField(default=timezone.now)
    forma_pago = models.CharField(max_length=20, choices=FORMA_PAGO_CHOICES, default='efectivo', null=True, blank=True)

    # Campos nuevos para módulo de caja
    estado_pago = models.CharField(max_length=20, choices=ESTADO_PAGO_CHOICES, default='pendiente')
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Monto ya pagado')
    propina = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Propina adicional')
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Descuento aplicado')
    descuento_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text='% de descuento')
    total_final = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Total con descuento y propina')

    observaciones = models.TextField(blank=True, null=True, help_text='Notas del pedido')
    observaciones_caja = models.TextField(blank=True, null=True, help_text='Notas del cajero')

    fecha_pago = models.DateTimeField(null=True, blank=True, help_text='Fecha y hora del pago')
    cajero_responsable = models.ForeignKey('usuarios.Usuario', on_delete=models.SET_NULL, null=True, blank=True, related_name='pedidos_cobrados')

    # ✅ NUEVO: Mesero que comandó el pedido
    mesero_comanda = models.ForeignKey('usuarios.Usuario', on_delete=models.SET_NULL, null=True, blank=True, related_name='pedidos_comandados', help_text='Mesero que tomó el pedido')
    numero_personas = models.PositiveIntegerField(default=1, help_text='Número de personas en la mesa')

    # Campos de auditoría
    modificado = models.BooleanField(default=False, help_text='Indica si el pedido fue modificado por caja')
    reasignado = models.BooleanField(default=False, help_text='Indica si fue reasignado a otra mesa')
    
    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
    
    def __str__(self):
        return f"Pedido #{self.id} - Mesa {self.mesa.numero if self.mesa else 'N/A'} - {self.get_estado_display()}"


class DetallePedido(models.Model):
    """Modelo para los detalles de pedidos"""
    # ✅ SOLUCIONADO: Usar related_name='detalles'
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey('productos.Producto', on_delete=models.PROTECT, related_name='detalles_pedidos')
    cantidad = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        verbose_name = 'Detalle de Pedido'
        verbose_name_plural = 'Detalles de Pedidos'
    
    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre if self.producto else 'Producto'} - Pedido #{self.pedido.id}"