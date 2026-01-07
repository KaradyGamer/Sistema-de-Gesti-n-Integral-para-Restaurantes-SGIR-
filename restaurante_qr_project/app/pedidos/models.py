from django.db import models
from django.utils import timezone

class Pedido(models.Model):
    # ✅ RONDA 2: Estados completos del ciclo de vida del pedido
    # Estados constantes (para usar en código sin hardcoding)
    ESTADO_CREADO = 'creado'
    ESTADO_CONFIRMADO = 'confirmado'
    ESTADO_EN_PREPARACION = 'en_preparacion'
    ESTADO_LISTO = 'listo'
    ESTADO_ENTREGADO = 'entregado'
    ESTADO_CANCELADO = 'cancelado'
    ESTADO_CERRADO = 'cerrado'

    ESTADO_CHOICES = [
        (ESTADO_CREADO, 'Creado'),
        (ESTADO_CONFIRMADO, 'Confirmado'),
        (ESTADO_EN_PREPARACION, 'En Preparación'),
        (ESTADO_LISTO, 'Listo'),
        (ESTADO_ENTREGADO, 'Entregado'),
        (ESTADO_CANCELADO, 'Cancelado'),
        (ESTADO_CERRADO, 'Cerrado'),
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
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default=ESTADO_CREADO)
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

    # ✅ RONDA 3A: Campos de cancelación
    motivo_cancelacion = models.TextField(blank=True, null=True, help_text='Motivo de cancelación del pedido')
    descuento_stock = models.BooleanField(default=False, help_text='Indica si ya se descontó stock para este pedido')

    # ✅ RONDA 3C: Campos de reembolso
    total_pagado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Total pagado acumulado (todas las transacciones)'
    )
    total_reembolsado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Total reembolsado acumulado'
    )
    reembolso_estado = models.CharField(
        max_length=10,
        default='none',
        choices=[
            ('none', 'Sin reembolso'),
            ('parcial', 'Reembolso parcial'),
            ('total', 'Reembolso total'),
        ],
        help_text='Estado del reembolso'
    )
    
    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
    
    def __str__(self):
        return f"Pedido #{self.id} - Mesa {self.mesa.numero if self.mesa else 'N/A'} - {self.get_estado_display()}"

    def calcular_total(self):
        """Calcula total desde detalles (útil si se modifican productos)"""
        return sum(detalle.subtotal for detalle in self.detalles.all())

    def todos_productos_pagados(self):
        """Verifica si TODOS los productos del pedido están completamente pagados"""
        return all(detalle.esta_pagado_completo for detalle in self.detalles.all())

    def productos_pendientes_pago(self):
        """Retorna lista de productos que aún tienen cantidad pendiente de pago"""
        return [
            {
                'producto': detalle.producto.nombre,
                'cantidad_total': detalle.cantidad,
                'cantidad_pagada': detalle.cantidad_pagada,
                'cantidad_pendiente': detalle.cantidad_pendiente,
                'precio_unitario': float(detalle.precio_unitario),
                'subtotal_pendiente': float(detalle.precio_unitario * detalle.cantidad_pendiente)
            }
            for detalle in self.detalles.all()
            if detalle.cantidad_pendiente > 0
        ]


class DetallePedido(models.Model):
    """Modelo para los detalles de pedidos"""
    # ✅ SOLUCIONADO: Usar related_name='detalles'
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey('productos.Producto', on_delete=models.PROTECT, related_name='detalles_pedidos')
    cantidad = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # ✅ NUEVO: Snapshot de precio unitario histórico
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Precio del producto al momento del pedido'
    )

    # ✅ NUEVO: Control de pago por producto individual
    cantidad_pagada = models.PositiveIntegerField(
        default=0,
        help_text='Cantidad de este producto ya pagada'
    )

    class Meta:
        verbose_name = 'Detalle de Pedido'
        verbose_name_plural = 'Detalles de Pedidos'

    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre if self.producto else 'Producto'} - Pedido #{self.pedido.id}"

    def save(self, *args, **kwargs):
        """Guardar snapshot de precio al crear"""
        if not self.precio_unitario and self.producto:
            self.precio_unitario = self.producto.precio
        if not self.subtotal:
            self.subtotal = self.precio_unitario * self.cantidad
        super().save(*args, **kwargs)

    @property
    def cantidad_pendiente(self):
        """Cantidad que aún falta por pagar"""
        return self.cantidad - self.cantidad_pagada

    @property
    def esta_pagado_completo(self):
        """Verifica si todo el detalle está pagado"""
        return self.cantidad_pagada >= self.cantidad