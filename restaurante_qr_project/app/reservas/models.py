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