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


# ══════════════════════════════════════════════
# 🧾 SGIR v40.4.0: MODELO CENTRAL - CUENTAMESA
# ══════════════════════════════════════════════

class CuentaMesa(models.Model):
    """
    Entidad central financiera del sistema.
    Una mesa puede tener múltiples pedidos, pero UNA sola cuenta abierta.

    Reglas:
    - Solo UNA cuenta ABIERTA por mesa (constraint en BD)
    - Todos los pedidos de la mesa se acumulan aquí
    - Los pagos se aplican a la cuenta, no a pedidos individuales
    - Cierre de cuenta puede dejar deuda autorizada con PIN secundario
    """

    ESTADO_CHOICES = [
        ('abierta', 'Abierta'),
        ('cerrada', 'Cerrada'),
        ('con_deuda', 'Cerrada con Deuda'),
        ('cancelada', 'Cancelada'),
    ]

    # Relaciones
    mesa = models.ForeignKey(
        'mesas.Mesa',
        on_delete=models.PROTECT,
        related_name='cuentas',
        help_text='Mesa asociada a esta cuenta'
    )

    # Estado y control
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='abierta',
        help_text='Estado de la cuenta'
    )

    # Montos
    total_acumulado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Suma de todos los pedidos de esta cuenta'
    )

    monto_pagado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Total pagado hasta el momento'
    )

    # Auditoría
    fecha_apertura = models.DateTimeField(
        default=timezone.now,
        help_text='Fecha y hora de apertura de la cuenta'
    )

    fecha_cierre = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Fecha y hora de cierre de la cuenta'
    )

    abierta_por = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        related_name='cuentas_abiertas',
        help_text='Usuario que abrió la cuenta (mesero/cliente)'
    )

    cerrada_por = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cuentas_cerradas',
        help_text='Usuario que cerró la cuenta (cajero)'
    )

    # Deuda autorizada
    deuda_autorizada = models.BooleanField(
        default=False,
        help_text='Si True, se cerró con deuda mediante PIN secundario'
    )

    autorizada_por = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deudas_autorizadas',
        help_text='Usuario que autorizó el cierre con deuda'
    )

    motivo_deuda = models.TextField(
        blank=True,
        null=True,
        help_text='Motivo por el que se autorizó cerrar con deuda'
    )

    observaciones = models.TextField(
        blank=True,
        null=True,
        help_text='Observaciones generales de la cuenta'
    )

    class Meta:
        verbose_name = 'Cuenta de Mesa'
        verbose_name_plural = 'Cuentas de Mesa'
        ordering = ['-fecha_apertura']

        # ✅ CRÍTICO: Solo UNA cuenta ABIERTA por mesa
        constraints = [
            models.UniqueConstraint(
                fields=['mesa'],
                condition=models.Q(estado='abierta'),
                name='unique_cuenta_abierta_por_mesa',
                violation_error_message='Ya existe una cuenta abierta para esta mesa'
            )
        ]

        indexes = [
            models.Index(fields=['mesa', 'estado']),
            models.Index(fields=['fecha_apertura']),
        ]

    def __str__(self):
        return f"Cuenta Mesa {self.mesa.numero} - {self.get_estado_display()} - Bs/ {self.total_acumulado}"

    @property
    def saldo(self):
        """Saldo pendiente (total - pagado)"""
        return self.total_acumulado - self.monto_pagado

    @property
    def esta_saldada(self):
        """Verifica si la cuenta está completamente pagada"""
        return self.saldo <= Decimal('0.00')

    def recalcular_totales(self):
        """
        v40.5.1: Recalcula total_acumulado y monto_pagado usando aggregate (SIN N+1).
        DEBE llamarse:
        - Al crear/eliminar pedido
        - Al crear/eliminar pago
        """
        from app.pedidos.models import Pedido
        from django.db.models import Sum, Q

        # v40.5.1: Usar aggregate para evitar queries N+1
        pedidos_agregados = self.pedidos.exclude(estado='cancelado').aggregate(
            total=Sum('total_final')
        )
        self.total_acumulado = Decimal(str(pedidos_agregados['total'] or 0))

        # v40.5.1: Calcular total de pagos PROCESADOS solamente
        pagos_agregados = self.pagos.filter(estado='procesado').aggregate(
            total=Sum('monto_total')
        )
        self.monto_pagado = Decimal(str(pagos_agregados['total'] or 0))

        self.save(update_fields=['total_acumulado', 'monto_pagado'])

    def cerrar_cuenta(self, usuario, pin_secundario_validado=False, motivo_deuda=None):
        """
        v40.5.1: Cierra la cuenta de la mesa de forma ATÓMICA.

        Args:
            usuario: Usuario que cierra la cuenta (cajero)
            pin_secundario_validado: Si se validó PIN para cerrar con deuda
            motivo_deuda: Motivo si se cierra con deuda

        Returns:
            bool: True si se cerró exitosamente

        Raises:
            ValidationError: Si no se puede cerrar
        """
        from django.core.exceptions import ValidationError
        from django.db import transaction

        # v40.5.1: Hacer toda la operación atómica con lock
        with transaction.atomic():
            # Lock de la cuenta actual
            cuenta_locked = CuentaMesa.objects.select_for_update().get(pk=self.pk)

            # Recalcular totales dentro del lock
            cuenta_locked.recalcular_totales()

            # Validar cierre
            if cuenta_locked.saldo > Decimal('0.00'):
                # Hay deuda pendiente
                if not pin_secundario_validado:
                    raise ValidationError(
                        f'No se puede cerrar la cuenta. Saldo pendiente: Bs/ {cuenta_locked.saldo:.2f}. '
                        f'Se requiere PIN secundario para autorizar cierre con deuda.'
                    )

                # Cerrar con deuda autorizada
                cuenta_locked.estado = 'con_deuda'
                cuenta_locked.deuda_autorizada = True
                cuenta_locked.autorizada_por = usuario
                cuenta_locked.motivo_deuda = motivo_deuda or 'Cierre con deuda autorizado'
                logger.warning(
                    f"Cuenta Mesa {cuenta_locked.mesa.numero} cerrada CON DEUDA: Bs/ {cuenta_locked.saldo:.2f} "
                    f"por {usuario.username}"
                )
            else:
                # Cerrar normalmente
                cuenta_locked.estado = 'cerrada'
                logger.info(f"Cuenta Mesa {cuenta_locked.mesa.numero} cerrada correctamente por {usuario.username}")

            cuenta_locked.fecha_cierre = timezone.now()
            cuenta_locked.cerrada_por = usuario
            cuenta_locked.save()

            # Liberar mesa dentro de la transacción
            from app.mesas.utils import liberar_mesa
            liberar_mesa(cuenta_locked.mesa)

            # Actualizar instancia actual
            self.refresh_from_db()

        return True


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
    pedido = models.ForeignKey(
        'pedidos.Pedido',
        on_delete=models.CASCADE,
        related_name='transacciones',
        null=True,  # ✅ v40.4.0: Ahora opcional (pagos a cuenta, no a pedido individual)
        blank=True
    )

    # ✅ SGIR v40.4.0: Relación con CuentaMesa (pagos se aplican a la cuenta)
    cuenta = models.ForeignKey(
        CuentaMesa,
        on_delete=models.PROTECT,
        related_name='pagos',
        help_text='Cuenta de mesa a la que se aplica este pago',
        null=True,  # Temporal para migración
        blank=True
    )

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
        v40.4.0: Valida que no haya CuentaMesa abiertas antes de cerrar.
        """
        from django.contrib.sessions.models import Session
        from django.utils import timezone as tz
        from django.core.exceptions import ValidationError

        # ✅ v40.4.0: Validar que NO haya cuentas ABIERTAS
        cuentas_abiertas = CuentaMesa.objects.filter(estado='abierta')

        if cuentas_abiertas.exists():
            # Generar lista detallada de cuentas abiertas
            lista_cuentas = []
            for cuenta in cuentas_abiertas[:5]:  # Mostrar máximo 5
                lista_cuentas.append(
                    f"Mesa {cuenta.mesa.numero} - "
                    f"Total: Bs/ {cuenta.total_acumulado:.2f}, Pagado: Bs/ {cuenta.monto_pagado:.2f}, "
                    f"Saldo: Bs/ {cuenta.saldo:.2f}"
                )

            raise ValidationError(
                f'No se puede cerrar la caja. Hay {cuentas_abiertas.count()} cuenta(s) abierta(s):\n' +
                '\n'.join(lista_cuentas) +
                '\n\nPor favor, cierre todas las cuentas antes de cerrar caja.'
            )

        # ⚠️ v40.4.0: PERMITIR (pero registrar) cuentas con deuda autorizada
        cuentas_con_deuda = CuentaMesa.objects.filter(estado='con_deuda')
        if cuentas_con_deuda.exists():
            import logging
            logger = logging.getLogger('app.caja')
            logger.warning(
                f"Cierre de caja con {cuentas_con_deuda.count()} cuenta(s) cerrada(s) con deuda. "
                f"Mesas: {', '.join(str(c.mesa.numero) for c in cuentas_con_deuda)}"
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
        empleados = Usuario.objects.filter(rol__in=['mesero', 'cocinero'])

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

        # ✅ FIX #4 v40.3.2: Validar DEUDA REAL antes de finalizar jornada
        from django.db.models import F, Q

        pedidos_con_deuda = Pedido.objects.filter(
            Q(estado_pago__in=['pendiente', 'parcial']) |
            Q(total_final__gt=F('monto_pagado'))
        ).exclude(
            estado='cancelado'
        )

        if pedidos_con_deuda.exists():
            # Generar lista detallada de pedidos con deuda
            lista_pedidos = ', '.join([
                f"Pedido #{p.id} (Mesa {p.mesa.numero if p.mesa else 'N/A'}) - Bs/ {p.total_final or p.total}"
                for p in pedidos_con_deuda[:5]  # Mostrar máximo 5
            ])

            raise ValidationError(
                f'No se puede finalizar la jornada laboral. '
                f'Hay {pedidos_con_deuda.count()} pedido(s) pendiente(s) de pago: {lista_pedidos}. '
                f'Por favor, procese todos los pagos antes de cerrar la jornada.'
            )

        self.estado = 'finalizada'
        self.hora_fin = timezone.now()
        self.finalizado_por = usuario
        if observaciones:
            self.observaciones_cierre = observaciones
        self.save()