"""
Modelos del módulo de Pedidos.

Este módulo gestiona el ciclo completo de vida de los pedidos en el restaurante:
- Creación y confirmación de pedidos
- Máquina de estados estricta (creado → confirmado → en_preparación → listo → entregado → cerrado)
- Control de pagos (pendiente, parcial, pagado)
- Sistema de cancelación con devolución de stock
- Reembolsos con autorización
- Modificaciones con auditoría completa

IMPORTANTE: La máquina de estados es ESTRICTA. No modificar transiciones sin validación.
"""
from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

class Pedido(models.Model):
    """
    Modelo principal de Pedido.

    Representa una comanda completa de una mesa, con control total del ciclo de vida:
    - Estados del pedido (máquina de estados estricta)
    - Control de pagos (total, parcial, pendiente)
    - Sistema de propinas y descuentos
    - Reembolsos y cancelaciones
    - Auditoría de modificaciones

    Flujo normal:
    1. creado (inicial)
    2. confirmado (mesero confirma)
    3. en_preparacion (cocina trabaja)
    4. listo (cocina termina)
    5. entregado (mesero entrega)
    6. cerrado (caja cobra y cierra)

    CRÍTICO: NO modificar estados sin pasar por las validaciones de negocio.
    """
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
        """
        Calcula el total del pedido sumando todos los detalles.

        Útil cuando se modifican productos o cantidades.

        Returns:
            Decimal: Suma de todos los subtotales de los detalles
        """
        return sum(detalle.subtotal for detalle in self.detalles.all())

    def todos_productos_pagados(self):
        """
        Verifica si TODOS los productos del pedido están completamente pagados.

        Valida que cada detalle tenga cantidad_pagada >= cantidad.

        Returns:
            bool: True si todos los productos están pagados completamente
        """
        return all(detalle.esta_pagado_completo for detalle in self.detalles.all())

    def productos_pendientes_pago(self):
        """
        Retorna lista de productos que aún tienen cantidad pendiente de pago.

        Útil para mostrar en el panel de caja qué productos faltan por cobrar
        en casos de pagos parciales.

        Returns:
            list: Lista de diccionarios con información de productos pendientes
                  Incluye: producto, cantidad_total, cantidad_pagada,
                  cantidad_pendiente, precio_unitario, subtotal_pendiente
        """
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

    # ========== MÁQUINA DE ESTADOS ESTRICTA ==========

    TRANSICIONES_VALIDAS = {
        ESTADO_CREADO: [ESTADO_CONFIRMADO, ESTADO_CANCELADO],
        ESTADO_CONFIRMADO: [ESTADO_EN_PREPARACION, ESTADO_CANCELADO],
        ESTADO_EN_PREPARACION: [ESTADO_LISTO, ESTADO_CANCELADO],
        ESTADO_LISTO: [ESTADO_ENTREGADO],
        ESTADO_ENTREGADO: [ESTADO_CERRADO],
        ESTADO_CANCELADO: [],  # Estado terminal
        ESTADO_CERRADO: [],  # Estado terminal
    }

    def puede_cambiar_a_estado(self, nuevo_estado):
        """
        Valida si el pedido puede cambiar al nuevo estado según la máquina de estados.

        Args:
            nuevo_estado (str): Estado destino

        Returns:
            bool: True si la transición es válida
        """
        if self.estado not in self.TRANSICIONES_VALIDAS:
            return False
        return nuevo_estado in self.TRANSICIONES_VALIDAS[self.estado]

    @transaction.atomic
    def cambiar_estado(self, nuevo_estado, usuario=None, motivo=None):
        """
        Cambia el estado del pedido validando la máquina de estados.

        Args:
            nuevo_estado (str): Estado destino
            usuario (Usuario, optional): Usuario que ejecuta el cambio
            motivo (str, optional): Motivo del cambio (obligatorio para cancelación)

        Raises:
            ValidationError: Si la transición no es válida
        """
        if not self.puede_cambiar_a_estado(nuevo_estado):
            raise ValidationError(
                f"No se puede cambiar de '{self.get_estado_display()}' a '{dict(self.ESTADO_CHOICES)[nuevo_estado]}'. "
                f"Transiciones válidas: {[dict(self.ESTADO_CHOICES)[e] for e in self.TRANSICIONES_VALIDAS[self.estado]]}"
            )

        # Validación específica para cancelación
        if nuevo_estado == self.ESTADO_CANCELADO:
            if not motivo:
                raise ValidationError("La cancelación requiere un motivo")
            self.motivo_cancelacion = motivo
            # Devolver stock si ya fue descontado
            if self.descuento_stock:
                self._devolver_stock()

        self.estado = nuevo_estado
        self.save()

    @transaction.atomic
    def confirmar(self, usuario=None):
        """
        Confirma el pedido y descuenta stock de inventario.

        Args:
            usuario (Usuario, optional): Usuario que confirma

        Raises:
            ValidationError: Si no se puede confirmar o no hay stock suficiente
        """
        self.cambiar_estado(self.ESTADO_CONFIRMADO, usuario)

        if not self.descuento_stock:
            self._descontar_stock()
            self.descuento_stock = True
            self.save()

    def _descontar_stock(self):
        """
        Descuenta stock de inventario para todos los detalles del pedido.

        CRÍTICO: Este método debe llamarse dentro de transaction.atomic

        Raises:
            ValidationError: Si no hay stock suficiente
        """
        from app.inventario.models import Insumo, MovimientoInventario

        for detalle in self.detalles.all():
            producto = detalle.producto

            # Verificar si el producto tiene receta (insumos)
            if hasattr(producto, 'receta') and producto.receta:
                for ingrediente in producto.receta.ingredientes.all():
                    insumo = ingrediente.insumo
                    cantidad_necesaria = ingrediente.cantidad * detalle.cantidad

                    if insumo.stock_actual < cantidad_necesaria:
                        raise ValidationError(
                            f"Stock insuficiente para '{insumo.nombre}'. "
                            f"Necesario: {cantidad_necesaria}, Disponible: {insumo.stock_actual}"
                        )

                    # Descontar stock
                    insumo.stock_actual -= cantidad_necesaria
                    insumo.save()

                    # Registrar movimiento
                    MovimientoInventario.objects.create(
                        insumo=insumo,
                        tipo='salida',
                        cantidad=cantidad_necesaria,
                        motivo=f'Pedido #{self.id}',
                        usuario=self.mesero_comanda
                    )

    def _devolver_stock(self):
        """
        Devuelve stock al inventario cuando se cancela un pedido.

        CRÍTICO: Este método debe llamarse dentro de transaction.atomic
        """
        from app.inventario.models import Insumo, MovimientoInventario

        for detalle in self.detalles.all():
            producto = detalle.producto

            if hasattr(producto, 'receta') and producto.receta:
                for ingrediente in producto.receta.ingredientes.all():
                    insumo = ingrediente.insumo
                    cantidad_devolver = ingrediente.cantidad * detalle.cantidad

                    # Devolver stock
                    insumo.stock_actual += cantidad_devolver
                    insumo.save()

                    # Registrar movimiento
                    MovimientoInventario.objects.create(
                        insumo=insumo,
                        tipo='entrada',
                        cantidad=cantidad_devolver,
                        motivo=f'Cancelación Pedido #{self.id}',
                        usuario=self.cajero_responsable
                    )

    @transaction.atomic
    def registrar_pago(self, monto, forma_pago='efectivo', cajero=None):
        """
        Registra un pago (total o parcial) para el pedido.

        Args:
            monto (Decimal): Monto pagado
            forma_pago (str): Método de pago
            cajero (Usuario, optional): Cajero que recibe el pago

        Raises:
            ValidationError: Si el pedido no está en estado válido para pagar
        """
        if self.estado not in [self.ESTADO_ENTREGADO, self.ESTADO_CONFIRMADO, self.ESTADO_EN_PREPARACION, self.ESTADO_LISTO]:
            raise ValidationError("Solo se pueden registrar pagos en pedidos entregados o en proceso")

        if self.estado_pago == 'pagado':
            raise ValidationError("Este pedido ya está completamente pagado")

        if monto <= 0:
            raise ValidationError("El monto debe ser mayor a cero")

        if monto < self.total_final * 0.01:  # Validar monto mínimo del 1%
            raise ValidationError(f"El pago parcial debe ser al menos el 1% del total (${self.total_final * 0.01:.2f})")

        self.monto_pagado += monto
        self.total_pagado += monto
        self.forma_pago = forma_pago
        self.cajero_responsable = cajero
        self.fecha_pago = timezone.now()

        # Actualizar estado de pago
        if self.monto_pagado >= self.total_final:
            self.estado_pago = 'pagado'
        elif self.monto_pagado > 0:
            self.estado_pago = 'parcial'

        self.save()

    @transaction.atomic
    def cerrar_pedido(self, cajero=None):
        """
        Cierra el pedido después de validar pago completo.

        Args:
            cajero (Usuario, optional): Cajero que cierra

        Raises:
            ValidationError: Si el pedido no está pagado completamente
        """
        if self.estado_pago != 'pagado':
            raise ValidationError("No se puede cerrar un pedido sin pago completo")

        if self.estado != self.ESTADO_ENTREGADO:
            raise ValidationError("Solo se pueden cerrar pedidos entregados")

        self.cambiar_estado(self.ESTADO_CERRADO, cajero)
        self.cajero_responsable = cajero
        self.save()


class DetallePedido(models.Model):
    """
    Modelo de Detalle de Pedido.

    Representa cada producto individual dentro de un pedido.
    Características importantes:
    - Snapshot de precio histórico (precio_unitario): guarda el precio al momento del pedido
    - Control de pago parcial por producto (cantidad_pagada vs cantidad)
    - Relación PROTECT con Producto (no se puede eliminar producto si está en pedidos)
    - Cálculo automático de subtotal al guardar

    Ejemplo:
        Si un pedido tiene 3 cervezas, este detalle tendrá:
        - cantidad = 3
        - precio_unitario = 15.00 (precio al momento del pedido)
        - subtotal = 45.00
        - cantidad_pagada = 0 (inicialmente)

    IMPORTANTE: El precio_unitario es un SNAPSHOT histórico. Aunque el producto
    cambie de precio posteriormente, el detalle mantiene el precio original.
    """
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
        """
        Guarda el detalle del pedido.

        Lógica automática:
        1. Si no existe precio_unitario, lo toma del producto actual (snapshot)
        2. Si no existe subtotal, lo calcula (precio_unitario * cantidad)

        CRÍTICO: El precio_unitario se guarda UNA VEZ al crear. No se actualiza
        aunque el producto cambie de precio. Esto mantiene integridad histórica.
        """
        if not self.precio_unitario and self.producto:
            self.precio_unitario = self.producto.precio
        if not self.subtotal:
            self.subtotal = self.precio_unitario * self.cantidad
        super().save(*args, **kwargs)

    @property
    def cantidad_pendiente(self):
        """
        Calcula la cantidad de productos que aún faltan por pagar.

        Returns:
            int: cantidad total - cantidad ya pagada

        Ejemplo:
            Si cantidad=5 y cantidad_pagada=2, retorna 3
        """
        return self.cantidad - self.cantidad_pagada

    @property
    def esta_pagado_completo(self):
        """
        Verifica si todo el detalle está completamente pagado.

        Returns:
            bool: True si cantidad_pagada >= cantidad

        Usado para validar si se puede cerrar el pedido o si se deben
        seguir aceptando pagos parciales.
        """
        return self.cantidad_pagada >= self.cantidad