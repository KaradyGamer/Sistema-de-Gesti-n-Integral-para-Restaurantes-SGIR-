from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
import logging

logger = logging.getLogger('app.caja')


# === SGIR v38.3: Constante Global de Métodos de Pago (unificada) ===
METODO_PAGO_CHOICES = [
    ('efectivo', 'Efectivo'),
    ('tarjeta', 'Tarjeta'),
    ('qr', 'Código QR'),
    ('movil', 'Pago Móvil'),
]


class Transaccion(models.Model):
    """
    Modelo para registrar transacciones de pago
    Cada pedido puede tener una o más transacciones (pagos mixtos)
    """
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('procesado', 'Procesado'),
        ('cancelado', 'Cancelado'),
        ('reembolsado', 'Reembolsado'),
    ]

    # Relaciones
    pedido = models.ForeignKey('pedidos.Pedido', on_delete=models.CASCADE, related_name='transacciones')
    cajero = models.ForeignKey('usuarios.Usuario', on_delete=models.SET_NULL, null=True, related_name='transacciones_realizadas')

    # Datos de la transacción
    monto_total = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='procesado')

    # Facturación
    numero_factura = models.CharField(max_length=50, unique=True, blank=True, null=True)
    comprobante_externo = models.ImageField(upload_to='comprobantes/', blank=True, null=True, help_text='Captura o foto del comprobante')

    # Datos adicionales
    referencia = models.CharField(max_length=100, blank=True, null=True, help_text='Referencia de pago digital')
    observaciones = models.TextField(blank=True, null=True)

    # Timestamps
    fecha_hora = models.DateTimeField(default=timezone.now)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Transacción'
        verbose_name_plural = 'Transacciones'
        ordering = ['-fecha_hora']

    def __str__(self):
        return f"Transacción #{self.id} - Pedido #{self.pedido.id} - Bs/ {self.monto_total}"


class DetallePago(models.Model):
    """
    Modelo para desglosar pagos mixtos
    Permite dividir un pago en múltiples métodos
    """
    transaccion = models.ForeignKey(Transaccion, on_delete=models.CASCADE, related_name='detalles_pago')
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES)
    monto = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    referencia = models.CharField(max_length=100, blank=True, null=True, help_text='Número de transacción, voucher, etc.')

    class Meta:
        verbose_name = 'Detalle de Pago'
        verbose_name_plural = 'Detalles de Pago'

    def __str__(self):
        return f"{self.get_metodo_pago_display()} - Bs/ {self.monto}"


class CierreCaja(models.Model):
    """
    Modelo para registrar cierres de caja por turno
    Permite cuadre y auditoría de ventas
    """
    TURNO_CHOICES = [
        ('manana', 'Mañana (06:00 - 14:00)'),
        ('tarde', 'Tarde (14:00 - 22:00)'),
        ('noche', 'Noche (22:00 - 06:00)'),
        ('completo', 'Día Completo'),
    ]

    ESTADO_CHOICES = [
        ('abierto', 'Abierto'),
        ('cerrado', 'Cerrado'),
    ]

    # Datos del cierre
    cajero = models.ForeignKey('usuarios.Usuario', on_delete=models.SET_NULL, null=True, related_name='cierres_caja')
    fecha = models.DateField(default=timezone.now)
    turno = models.CharField(max_length=20, choices=TURNO_CHOICES)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='abierto')

    # Montos iniciales
    efectivo_inicial = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Efectivo al abrir caja')

    # Montos de ventas por método
    total_efectivo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_tarjeta = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_qr = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_movil = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Totales y diferencias
    total_ventas = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Suma de todos los métodos')
    efectivo_esperado = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Inicial + ventas efectivo')
    efectivo_real = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Efectivo contado físicamente')
    diferencia = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Real - Esperado')

    # Información adicional
    total_descuentos = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_propinas = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    numero_pedidos = models.IntegerField(default=0, help_text='Total de pedidos en el turno')

    observaciones = models.TextField(blank=True, null=True)

    # Timestamps
    hora_apertura = models.DateTimeField(default=timezone.now)
    hora_cierre = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Cierre de Caja'
        verbose_name_plural = 'Cierres de Caja'
        ordering = ['-fecha', '-hora_apertura']
        unique_together = [['cajero', 'fecha', 'turno']]  # Un cajero solo puede tener un turno por día

    def __str__(self):
        return f"Cierre {self.fecha} - {self.get_turno_display()} - {self.cajero}"

    def calcular_diferencia(self):
        """Calcula la diferencia entre efectivo esperado y real"""
        self.diferencia = self.efectivo_real - self.efectivo_esperado
        return self.diferencia

    def cerrar_caja(self, efectivo_real, observaciones=None):
        """
        Cierra el turno de caja y cierra todas las sesiones activas.
        Valida que no haya pedidos pendientes antes de cerrar.
        """
        from django.contrib.sessions.models import Session
        from django.utils import timezone as tz
        from app.pedidos.models import Pedido
        from django.core.exceptions import ValidationError

        # ✅ NUEVO: Validar que no haya pedidos pendientes (usando constantes válidas)
        pedidos_pendientes = Pedido.objects.filter(
            estado__in=[
                Pedido.ESTADO_CREADO,
                Pedido.ESTADO_CONFIRMADO,
                Pedido.ESTADO_EN_PREPARACION,
                Pedido.ESTADO_LISTO,
                Pedido.ESTADO_ENTREGADO
            ]
        ).count()

        if pedidos_pendientes > 0:
            raise ValidationError(
                f'No se puede cerrar la caja. Hay {pedidos_pendientes} pedido(s) pendiente(s) de pago. '
                f'Por favor, procese todos los pagos antes de cerrar caja.'
            )

        self.efectivo_real = efectivo_real
        self.diferencia = self.calcular_diferencia()
        self.estado = 'cerrado'
        self.hora_cierre = timezone.now()
        if observaciones:
            self.observaciones = observaciones
        self.save()

        # Cerrar todas las sesiones activas de empleados (excepto admins y cajeros)
        from app.usuarios.models import Usuario

        # Obtener todas las sesiones activas
        sesiones_activas = Session.objects.filter(expire_date__gte=tz.now())

        for sesion in sesiones_activas:
            data = sesion.get_decoded()
            user_id = data.get('_auth_user_id')
            if user_id:
                try:
                    usuario = Usuario.objects.get(id=user_id)
                    if usuario.rol in ['mesero', 'cocinero']:
                        # Eliminar la sesión
                        sesion.delete()
                        logger.info(f"✅ Sesión cerrada para {usuario.username}")
                except Usuario.DoesNotExist:
                    pass


class HistorialModificacion(models.Model):
    """
    Modelo para auditoría de modificaciones a pedidos
    Registra quién, cuándo y qué cambió en un pedido
    """
    TIPO_CAMBIO_CHOICES = [
        ('agregar_producto', 'Agregar Producto'),
        ('eliminar_producto', 'Eliminar Producto'),
        ('modificar_cantidad', 'Modificar Cantidad'),
        ('aplicar_descuento', 'Aplicar Descuento'),
        ('agregar_propina', 'Agregar Propina'),
        ('reasignar_mesa', 'Reasignar Mesa'),
        ('cancelar_pedido', 'Cancelar Pedido'),
        ('otro', 'Otro'),
    ]

    # Relaciones
    pedido = models.ForeignKey('pedidos.Pedido', on_delete=models.CASCADE, related_name='historial_modificaciones')
    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.SET_NULL, null=True, related_name='modificaciones_realizadas')

    # Datos del cambio
    tipo_cambio = models.CharField(max_length=30, choices=TIPO_CAMBIO_CHOICES)
    detalle_anterior = models.JSONField(help_text='Estado antes del cambio')
    detalle_nuevo = models.JSONField(help_text='Estado después del cambio')
    motivo = models.TextField(blank=True, null=True, help_text='Razón del cambio')

    # Timestamp
    fecha_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Historial de Modificación'
        verbose_name_plural = 'Historial de Modificaciones'
        ordering = ['-fecha_hora']

    def __str__(self):
        return f"{self.get_tipo_cambio_display()} - Pedido #{self.pedido.id} - {self.fecha_hora.strftime('%d/%m/%Y %H:%M')}"


class AlertaStock(models.Model):
    """
    Modelo para alertas de productos con stock bajo o agotados
    """
    TIPO_ALERTA_CHOICES = [
        ('stock_bajo', 'Stock Bajo'),
        ('agotado', 'Agotado'),
        ('reposicion', 'Necesita Reposición'),
    ]

    ESTADO_CHOICES = [
        ('activa', 'Activa'),
        ('resuelta', 'Resuelta'),
        ('ignorada', 'Ignorada'),
    ]

    producto = models.ForeignKey('productos.Producto', on_delete=models.SET_NULL, null=True, related_name='alertas_stock')
    producto_nombre = models.CharField(max_length=100, default='Producto sin nombre', help_text='Nombre del producto (guardado para historial)')
    tipo_alerta = models.CharField(max_length=20, choices=TIPO_ALERTA_CHOICES)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activa')
    stock_actual = models.IntegerField(help_text='Stock al momento de crear la alerta')

    observaciones = models.TextField(blank=True, null=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_resolucion = models.DateTimeField(null=True, blank=True)
    resuelto_por = models.ForeignKey('usuarios.Usuario', on_delete=models.SET_NULL, null=True, blank=True, related_name='alertas_resueltas')

    class Meta:
        verbose_name = 'Alerta de Stock'
        verbose_name_plural = 'Alertas de Stock'
        ordering = ['-fecha_creacion']

    def __str__(self):
        nombre = self.producto.nombre if self.producto else self.producto_nombre
        return f"{nombre} - {self.get_tipo_alerta_display()} - {self.get_estado_display()}"

    def resolver(self, usuario, observaciones=None):
        """Marca la alerta como resuelta"""
        self.estado = 'resuelta'
        self.fecha_resolucion = timezone.now()
        self.resuelto_por = usuario
        if observaciones:
            self.observaciones = observaciones
        self.save()


class JornadaLaboral(models.Model):
    """
    Modelo para controlar la jornada laboral del restaurante
    Solo puede haber UNA jornada activa a la vez
    """
    ESTADO_CHOICES = [
        ('activa', 'Activa'),
        ('finalizada', 'Finalizada'),
    ]

    # Datos de la jornada
    cajero = models.ForeignKey('usuarios.Usuario', on_delete=models.SET_NULL, null=True, related_name='jornadas_iniciadas')
    fecha = models.DateField(default=timezone.now)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activa')

    # Timestamps
    hora_inicio = models.DateTimeField(default=timezone.now)
    hora_fin = models.DateTimeField(null=True, blank=True)

    # Información adicional
    observaciones_apertura = models.TextField(blank=True, null=True)
    observaciones_cierre = models.TextField(blank=True, null=True)
    finalizado_por = models.ForeignKey('usuarios.Usuario', on_delete=models.SET_NULL, null=True, blank=True, related_name='jornadas_finalizadas')

    class Meta:
        verbose_name = 'Jornada Laboral'
        verbose_name_plural = 'Jornadas Laborales'
        ordering = ['-fecha', '-hora_inicio']

    def __str__(self):
        return f"Jornada {self.fecha} - {self.get_estado_display()}"

    @classmethod
    def jornada_activa(cls):
        """Retorna la jornada activa o None"""
        return cls.objects.filter(estado='activa').first()

    @classmethod
    def hay_jornada_activa(cls):
        """Verifica si hay una jornada activa"""
        return cls.objects.filter(estado='activa').exists()

    def finalizar(self, usuario, observaciones=None):
        """
        Finaliza la jornada laboral.
        Valida que no haya pedidos pendientes DE PAGO antes de finalizar.
        """
        from app.pedidos.models import Pedido
        from django.core.exceptions import ValidationError

        # ✅ CORREGIDO: Validar por estado_pago (no por estado de comanda)
        # Solo impide finalizar si hay pedidos sin pagar (pendiente o parcial)
        pedidos_pendientes = Pedido.objects.filter(
            estado_pago='pendiente'
        ).exclude(
            estado='cancelado'
        )

        if pedidos_pendientes.exists():
            # Generar lista detallada de pedidos pendientes
            lista_pedidos = ', '.join([
                f"Pedido #{p.id} (Mesa {p.mesa.numero if p.mesa else 'N/A'}) - Bs/ {p.total_final or p.total}"
                for p in pedidos_pendientes[:5]  # Mostrar máximo 5
            ])

            raise ValidationError(
                f'No se puede finalizar la jornada laboral. '
                f'Hay {pedidos_pendientes.count()} pedido(s) pendiente(s) de pago: {lista_pedidos}. '
                f'Por favor, procese todos los pagos antes de cerrar la jornada.'
            )

        self.estado = 'finalizada'
        self.hora_fin = timezone.now()
        self.finalizado_por = usuario
        if observaciones:
            self.observaciones_cierre = observaciones
        self.save()

class Reembolso(models.Model):
    """
    Modelo para registrar reembolsos de pedidos.
    Permite reembolsos parciales o totales con autorización.
    """
    METODO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('qr', 'Código QR'),
        ('tarjeta', 'Tarjeta'),
        ('movil', 'Pago Móvil'),
    ]

    # Relaciones
    pedido = models.ForeignKey(
        'pedidos.Pedido',
        on_delete=models.CASCADE,
        related_name='reembolsos'
    )
    creado_por = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.PROTECT,
        related_name='reembolsos_creados'
    )
    autorizado_por = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='reembolsos_autorizados'
    )

    # Datos del reembolso
    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    metodo = models.CharField(max_length=20, choices=METODO_CHOICES)
    motivo = models.TextField(help_text='Razón del reembolso')
    codigo_autorizacion = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text='Código PIN o token de autorización'
    )

    # Timestamps
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Reembolso'
        verbose_name_plural = 'Reembolsos'
        ordering = ['-creado_en']

    def __str__(self):
        return f"Reembolso #{self.id} - Pedido #{self.pedido.id} - Bs/ {self.monto}"
