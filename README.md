"""
Modelos del módulo de Caja.

Este módulo gestiona todo el sistema de caja del restaurante:
- Transacciones y pagos (efectivo, tarjeta, QR, móvil, mixto)
- Cierres de caja por turno (mañana, tarde, noche, completo)
- Jornada laboral (solo UNA activa a la vez)
- Auditoría de modificaciones en pedidos
- Alertas de stock bajo/agotado
- Reembolsos con autorización

CRÍTICO: Este módulo es el núcleo financiero del sistema.
NO modificar sin validación exhaustiva de lógica de negocio.
"""
from django.db import models, transaction
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
import logging

logger = logging.getLogger('app.caja')


# === SGIR v38.3: Constante Global de Métodos de Pago (unificada) ===
# Estos métodos de pago se usan en múltiples modelos (Transaccion, DetallePago, Reembolso)
METODO_PAGO_CHOICES = [
    ('efectivo', 'Efectivo'),
    ('tarjeta', 'Tarjeta'),
    ('qr', 'Código QR'),
    ('movil', 'Pago Móvil'),
]


class Transaccion(models.Model):
    """
    Modelo de Transacción de Pago.

    Registra cada pago realizado en el sistema. Un pedido puede tener múltiples
    transacciones (por ejemplo, en pagos parciales o mixtos).

    Características:
    - Soporta múltiples métodos de pago
    - Permite pagos mixtos mediante DetallePago
    - Control de estados (pendiente, procesado, cancelado, reembolsado)
    - Facturación con número único
    - Comprobantes digitales (imagen/PDF)
    - Auditoría completa con timestamps

    Estados del ciclo de vida:
    - pendiente: Pago iniciado pero no confirmado
    - procesado: Pago exitoso y confirmado
    - cancelado: Pago anulado
    - reembolsado: Dinero devuelto al cliente

    IMPORTANTE: Cada transacción debe tener un cajero responsable para auditoría.
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
    Modelo de Cierre de Caja por Turno.

    Gestiona el cierre y cuadre de caja al finalizar cada turno de trabajo.

    Turnos soportados:
    - Mañana: 06:00 - 14:00
    - Tarde: 14:00 - 22:00
    - Noche: 22:00 - 06:00
    - Completo: Día completo (24h)

    Funcionalidades:
    - Cuadre de efectivo (inicial + ventas vs contado físico)
    - Cálculo automático de diferencias
    - Totales por método de pago
    - Validación: NO permite cerrar con pedidos pendientes
    - Al cerrar: cierra automáticamente sesiones de meseros y cocineros
    - Control de descuentos y propinas
    - Auditoría completa

    Validación única: Un cajero solo puede tener UN cierre por turno por día.

    CRÍTICO: El método cerrar_caja() valida que NO haya pedidos sin pagar
    antes de permitir el cierre. Esta validación NO debe eliminarse.
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
        """
        Calcula la diferencia entre efectivo esperado y real.

        Fórmula: diferencia = efectivo_real - efectivo_esperado

        Returns:
            Decimal: Diferencia (positivo = sobra, negativo = falta)
        """
        self.diferencia = self.efectivo_real - self.efectivo_esperado
        return self.diferencia

    def cerrar_caja(self, efectivo_real, observaciones=None):
        """
        Cierra el turno de caja y finaliza sesiones activas de empleados.

        Proceso:
        1. Valida que NO haya pedidos pendientes de pago
        2. Registra el efectivo contado físicamente
        3. Calcula la diferencia
        4. Marca el cierre como 'cerrado'
        5. Cierra automáticamente sesiones de meseros y cocineros

        Args:
            efectivo_real (Decimal): Efectivo contado físicamente en caja
            observaciones (str, optional): Notas adicionales del cierre

        Raises:
            ValidationError: Si hay pedidos pendientes de pago

        CRÍTICO: Esta validación es OBLIGATORIA para evitar pérdidas.
        NO eliminar la validación de pedidos pendientes.
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
    Modelo de Auditoría de Modificaciones.

    Registra TODOS los cambios realizados a los pedidos para trazabilidad
    y auditoría completa.

    Tipos de cambios registrados:
    - Agregar producto
    - Eliminar producto
    - Modificar cantidad
    - Aplicar descuento
    - Agregar propina
    - Reasignar mesa
    - Cancelar pedido
    - Otros cambios

    Información guardada:
    - Quién hizo el cambio (usuario)
    - Cuándo se hizo (fecha_hora automática)
    - Qué cambió (detalle_anterior y detalle_nuevo en JSON)
    - Por qué (motivo)

    Este registro es INMUTABLE (no se puede editar ni eliminar).
    Sirve para resolver disputas y auditorías internas.
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
    Modelo de Alertas de Stock.

    Sistema automático de alertas cuando productos tienen stock bajo o
    están agotados.

    Tipos de alerta:
    - stock_bajo: Producto por debajo del stock mínimo
    - agotado: Producto sin stock (cantidad = 0)
    - reposicion: Necesita reposición urgente

    Estados:
    - activa: Alerta pendiente de atención
    - resuelta: Stock repuesto
    - ignorada: Alerta descartada

    Funcionalidades:
    - Generación automática cuando stock baja
    - Guardado del nombre del producto (historial)
    - Resolución con usuario y fecha
    - Observaciones del encargado

    IMPORTANTE: Estas alertas se generan automáticamente desde el
    modelo de Producto e Insumo. NO crear manualmente.
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
        """
        Marca la alerta como resuelta.

        Args:
            usuario (Usuario): Usuario que resuelve la alerta
            observaciones (str, optional): Notas sobre la resolución

        Se ejecuta cuando se repone el stock y se verifica que
        el producto ya no está en estado crítico.
        """
        self.estado = 'resuelta'
        self.fecha_resolucion = timezone.now()
        self.resuelto_por = usuario
        if observaciones:
            self.observaciones = observaciones
        self.save()


class JornadaLaboral(models.Model):
    """
    Modelo de Jornada Laboral del Restaurante.

    Controla la apertura y cierre del restaurante. Solo puede existir
    UNA jornada activa a la vez en todo el sistema.

    Funcionalidades:
    - Control de jornada única activa
    - Validación: NO permite finalizar con pedidos sin pagar
    - Auditoría de quién abre y cierra
    - Observaciones de apertura y cierre
    - Integración con middleware para bloquear acceso de empleados
      cuando NO hay jornada activa

    Flujo normal:
    1. Cajero abre jornada (estado='activa')
    2. Empleados pueden trabajar (middleware lo valida)
    3. Cajero finaliza jornada (valida pedidos pendientes)
    4. Sesiones de meseros/cocineros se cierran automáticamente

    CRÍTICO: El middleware JornadaLaboralMiddleware depende de este modelo.
    Meseros y cocineros NO pueden acceder sin jornada activa.
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
        """
        Obtiene la jornada activa actual.

        Returns:
            JornadaLaboral or None: La jornada activa o None si no hay ninguna

        NOTA: Solo puede haber UNA jornada activa a la vez.
        """
        return cls.objects.filter(estado='activa').first()

    @classmethod
    def hay_jornada_activa(cls):
        """
        Verifica si existe una jornada activa.

        Returns:
            bool: True si hay una jornada activa

        Usado por el middleware para validar acceso de empleados.
        """
        return cls.objects.filter(estado='activa').exists()

    def finalizar(self, usuario, observaciones=None, forzar=False):
        """
        Finaliza la jornada laboral del día.

        Proceso:
        1. Valida que NO haya pedidos pendientes de pago (estado_pago='pendiente')
        2. Permite pedidos en preparación/listos (siempre que estén pagados)
        3. Marca la jornada como 'finalizada'
        4. Registra quién finalizó y cuándo

        Args:
            usuario (Usuario): Usuario que finaliza la jornada
            observaciones (str, optional): Notas del cierre
            forzar (bool, optional): Si True, permite cerrar incluso con pedidos pendientes (SOLO EMERGENCIAS)

        Raises:
            ValidationError: Si hay pedidos pendientes de pago y forzar=False

        CRÍTICO: Esta validación previene que se cierre el restaurante
        con deudas pendientes. NO eliminar la validación.
        """
        from app.pedidos.models import Pedido

        # ✅ CORREGIDO: Validar por estado_pago (no por estado de comanda)
        # Solo impide finalizar si hay pedidos sin pagar (pendiente o parcial)
        pedidos_pendientes = Pedido.objects.filter(
            estado_pago='pendiente'
        ).exclude(
            estado='cancelado'
        )

        if pedidos_pendientes.exists() and not forzar:
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
        if forzar and pedidos_pendientes.exists():
            self.observaciones_cierre = f"{observaciones or ''}\n\n[CIERRE FORZADO] Con {pedidos_pendientes.count()} pedido(s) pendiente(s)"
        self.save()

    @classmethod
    @transaction.atomic
    def recuperar_jornada_zombie(cls, usuario_autorizador):
        """
        Cierra forzadamente jornadas activas antiguas (modo recuperación).

        Uso: Solo en emergencias cuando una jornada queda "zombie" y bloquea el sistema.

        Args:
            usuario_autorizador (Usuario): Usuario con permisos de gerente/admin

        Returns:
            int: Número de jornadas cerradas

        Raises:
            ValidationError: Si el usuario no tiene permisos
        """
        if not usuario_autorizador.is_staff and not hasattr(usuario_autorizador, 'rol'):
            raise ValidationError("Solo gerentes o administradores pueden recuperar jornadas zombie")

        # Buscar jornadas activas con más de 24 horas
        hace_24h = timezone.now() - timezone.timedelta(hours=24)
        jornadas_zombie = cls.objects.filter(
            estado='activa',
            hora_inicio__lt=hace_24h
        )

        count = jornadas_zombie.count()
        for jornada in jornadas_zombie:
            jornada.finalizar(
                usuario=usuario_autorizador,
                observaciones="[RECUPERACIÓN AUTOMÁTICA] Jornada zombie cerrada por sistema",
                forzar=True
            )

        logger.warning(f"Recuperadas {count} jornada(s) zombie por {usuario_autorizador.username}")
        return count

class Reembolso(models.Model):
    """
    Modelo de Reembolsos.

    Gestiona la devolución de dinero a clientes por pedidos cancelados,
    productos no entregados, o errores del restaurante.

    Características:
    - Reembolsos parciales o totales
    - Requiere autorización de gerente o admin
    - Código de autorización obligatorio (PIN, token, etc.)
    - Motivo detallado del reembolso
    - Método de devolución (mismo método de pago original)
    - Auditoría completa (quién creó, quién autorizó, cuándo)

    Flujo:
    1. Cajero crea solicitud de reembolso con motivo
    2. Gerente/Admin ingresa código de autorización
    3. Se registra el reembolso
    4. Se actualiza el pedido (total_reembolsado, reembolso_estado)

    CRÍTICO: Los reembolsos son IRREVERSIBLES. Validar bien antes de crear.
    Siempre requieren autorización de nivel gerente o superior.
    """
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente de Autorización'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    ]

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
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente',
        help_text='Estado del reembolso'
    )
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
    autorizado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Reembolso'
        verbose_name_plural = 'Reembolsos'
        ordering = ['-creado_en']

    def __str__(self):
        return f"Reembolso #{self.id} - Pedido #{self.pedido.id} - Bs/ {self.monto} - {self.get_estado_display()}"

    @transaction.atomic
    def aprobar(self, autorizador, codigo_autorizacion):
        """
        Aprueba el reembolso con autorización de gerente.

        Args:
            autorizador (Usuario): Usuario con permisos de gerente/admin
            codigo_autorizacion (str): Código PIN o token de autorización

        Raises:
            ValidationError: Si el usuario no tiene permisos o el código es inválido
        """
        if self.estado != 'pendiente':
            raise ValidationError(f"No se puede aprobar un reembolso en estado '{self.get_estado_display()}'")

        # Validar permisos del autorizador
        if not autorizador.is_staff and not autorizador.rol in ['gerente', 'admin']:
            raise ValidationError("Solo gerentes o administradores pueden autorizar reembolsos")

        if not codigo_autorizacion:
            raise ValidationError("Se requiere código de autorización")

        self.estado = 'aprobado'
        self.autorizado_por = autorizador
        self.codigo_autorizacion = codigo_autorizacion
        self.autorizado_en = timezone.now()
        self.save()

        # Actualizar el pedido
        self.pedido.total_reembolsado += self.monto
        if self.pedido.total_reembolsado >= self.pedido.total_pagado:
            self.pedido.reembolso_estado = 'total'
        else:
            self.pedido.reembolso_estado = 'parcial'
        self.pedido.save()

    @transaction.atomic
    def rechazar(self, autorizador, motivo_rechazo):
        """
        Rechaza el reembolso.

        Args:
            autorizador (Usuario): Usuario con permisos de gerente/admin
            motivo_rechazo (str): Motivo del rechazo

        Raises:
            ValidationError: Si el usuario no tiene permisos
        """
        if self.estado != 'pendiente':
            raise ValidationError(f"No se puede rechazar un reembolso en estado '{self.get_estado_display()}'")

        # Validar permisos del autorizador
        if not autorizador.is_staff and not autorizador.rol in ['gerente', 'admin']:
            raise ValidationError("Solo gerentes o administradores pueden rechazar reembolsos")

        self.estado = 'rechazado'
        self.autorizado_por = autorizador
        self.motivo += f"\n\nMOTIVO DE RECHAZO: {motivo_rechazo}"
        self.autorizado_en = timezone.now()
        self.save()
