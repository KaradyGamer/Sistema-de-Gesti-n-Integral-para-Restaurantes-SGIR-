"""
Modelos del módulo de Reservas.

Gestiona las reservas de mesas del restaurante:
- Estados: pendiente, confirmada, en_progreso, completada, cancelada, no_presentado
- Validaciones de disponibilidad (no solapar reservas)
- Asignación automática de mesas según capacidad
- Control de vigencia (no permitir reservas pasadas)
- Integración con Mesas y Pedidos

IMPORTANTE: Las reservas tienen ventana de tolerancia (15 min) y se marcan
automáticamente como no_presentado si no se confirma a tiempo.
"""
from django.db import models
from django.core.validators import MinValueValidator
from app.mesas.models import Mesa
from django.utils import timezone
from datetime import datetime, timedelta

class Reserva(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('en_uso', 'En Uso'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
        ('no_show', 'No Show'),
    ]
    
    # Datos del cliente
    numero_carnet = models.CharField(max_length=20, verbose_name="Número de Carnet/CI")
    nombre_completo = models.CharField(max_length=100, verbose_name="Nombre Completo")
    telefono = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    
    # Datos de la reserva
    fecha_reserva = models.DateField(verbose_name="Fecha de Reserva")
    hora_reserva = models.TimeField(verbose_name="Hora de Reserva")
    numero_personas = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Número de Personas"
    )
    
    # Relación con mesa
    mesa = models.ForeignKey(
        Mesa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Mesa Asignada",
        related_name='reservas'
    )
    
    # Control de la reserva
    estado = models.CharField(
        max_length=15,
        choices=ESTADO_CHOICES,
        default='pendiente'
    )
    observaciones = models.TextField(blank=True, null=True)
    
    # Timestamps
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        ordering = ['-fecha_reserva', '-hora_reserva']
    
    def __str__(self):
        return f"{self.nombre_completo} - {self.fecha_reserva} {self.hora_reserva}"
    
    @property
    def datetime_reserva(self):
        """Combina fecha y hora en un datetime"""
        return datetime.combine(self.fecha_reserva, self.hora_reserva)

    def puede_cancelar(self):
        """Verifica si la reserva puede ser cancelada (al menos 2 horas antes)"""
        ahora = timezone.now()
        reserva_datetime = self.datetime_reserva

        # ✅ CORREGIDO: Solo hacer aware si no lo está ya
        if timezone.is_naive(reserva_datetime):
            reserva_datetime = timezone.make_aware(reserva_datetime)

        return reserva_datetime > ahora + timedelta(hours=2)

    def esta_vencida(self):
        """Verifica si la reserva ya pasó"""
        ahora = timezone.now()
        reserva_datetime = self.datetime_reserva

        # ✅ CORREGIDO: Solo hacer aware si no lo está ya
        if timezone.is_naive(reserva_datetime):
            reserva_datetime = timezone.make_aware(reserva_datetime)

        return reserva_datetime < ahora

    def esta_vencida_con_tolerancia(self, minutos_tolerancia=15):
        """
        Verifica si la reserva ya pasó considerando tiempo de tolerancia.

        Args:
            minutos_tolerancia (int): Minutos de tolerancia después de la hora reservada (default: 15)

        Returns:
            bool: True si ya pasó la hora + tolerancia
        """
        ahora = timezone.now()
        reserva_datetime = self.datetime_reserva

        # ✅ CORREGIDO: Solo hacer aware si no lo está ya
        if timezone.is_naive(reserva_datetime):
            reserva_datetime = timezone.make_aware(reserva_datetime)

        # Agregar tiempo de tolerancia
        hora_limite = reserva_datetime + timedelta(minutes=minutos_tolerancia)

        return ahora > hora_limite

    def liberar_por_no_show(self):
        """
        Libera la mesa si el cliente no llegó después del tiempo de tolerancia (15 min).
        Cambia el estado a 'no_show' y libera la mesa.
        """
        if not self.esta_vencida_con_tolerancia():
            return False  # Aún está en tiempo de tolerancia

        if self.estado not in ['pendiente', 'confirmada']:
            return False  # Solo liberar reservas que estaban esperando al cliente

        # Cambiar estado a no_show
        self.estado = 'no_show'
        self.save()

        # Liberar la mesa si estaba asignada
        if self.mesa:
            from app.mesas.utils import liberar_mesa
            liberar_mesa(self.mesa)
            logger = __import__('logging').getLogger('app.reservas')
            logger.info(
                f"Mesa {self.mesa.numero} liberada por no-show de reserva #{self.id} "
                f"({self.nombre_completo}) - Hora reserva: {self.hora_reserva}"
            )

        return True

    def validar_solapamiento(self, duracion_reserva_horas=2):
        """
        Valida que no haya otra reserva activa en la misma mesa al mismo tiempo.

        Args:
            duracion_reserva_horas: Duración estimada de la reserva en horas (default: 2)

        Returns:
            tuple: (es_valida, mensaje_error)
        """
        if not self.mesa:
            return (True, None)  # Sin mesa asignada, no hay solapamiento

        # Calcular inicio y fin de esta reserva
        inicio_reserva = self.datetime_reserva
        if timezone.is_naive(inicio_reserva):
            inicio_reserva = timezone.make_aware(inicio_reserva)

        fin_reserva = inicio_reserva + timedelta(hours=duracion_reserva_horas)

        # Buscar reservas que NO están canceladas o completadas
        reservas_activas = Reserva.objects.filter(
            mesa=self.mesa,
            fecha_reserva=self.fecha_reserva,
            estado__in=['pendiente', 'confirmada', 'en_uso']
        )

        # Excluir esta misma reserva si ya existe (para edición)
        if self.pk:
            reservas_activas = reservas_activas.exclude(pk=self.pk)

        # Verificar solapamiento con cada reserva activa
        for reserva in reservas_activas:
            inicio_otra = reserva.datetime_reserva
            if timezone.is_naive(inicio_otra):
                inicio_otra = timezone.make_aware(inicio_otra)

            fin_otra = inicio_otra + timedelta(hours=duracion_reserva_horas)

            # Detectar solapamiento:
            # Las reservas se solapan si inicio_reserva < fin_otra Y fin_reserva > inicio_otra
            if inicio_reserva < fin_otra and fin_reserva > inicio_otra:
                return (
                    False,
                    f"Mesa {self.mesa.numero} ya tiene reserva de {reserva.nombre_completo} "
                    f"a las {reserva.hora_reserva.strftime('%H:%M')}. "
                    f"Las reservas se solapan (duración estimada: {duracion_reserva_horas}h)"
                )

        return (True, None)

    def save(self, *args, **kwargs):
        """Override save para validar solapamiento antes de guardar"""
        # Validar solapamiento solo si la reserva no está cancelada/completada
        if self.estado in ['pendiente', 'confirmada', 'en_uso']:
            es_valida, mensaje = self.validar_solapamiento()
            if not es_valida:
                from django.core.exceptions import ValidationError
                raise ValidationError(mensaje)

        super().save(*args, **kwargs)