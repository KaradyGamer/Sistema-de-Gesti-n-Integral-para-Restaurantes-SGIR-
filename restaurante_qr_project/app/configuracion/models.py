from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import logging

logger = logging.getLogger(__name__)


class ConfiguracionSistema(models.Model):
    """
    Configuración global del sistema (Singleton).
    Solo debe existir 1 registro.
    """

    # Información del negocio
    nombre = models.CharField(
        max_length=200,
        default="Restaurante QR",
        help_text="Nombre del restaurante"
    )
    nit = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="NIT del negocio"
    )
    direccion = models.TextField(
        blank=True,
        null=True,
        help_text="Dirección del local"
    )
    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Teléfono de contacto"
    )
    email = models.EmailField(
        blank=True,
        null=True,
        help_text="Email de contacto"
    )
    logo = models.ImageField(
        upload_to='configuracion/logos/',
        blank=True,
        null=True,
        help_text="Logo del restaurante"
    )
    lema = models.CharField(
        max_length=300,
        blank=True,
        null=True,
        help_text="Lema o eslogan del restaurante"
    )

    # Configuración financiera
    moneda = models.CharField(
        max_length=10,
        default="Bs/",
        help_text="Símbolo de moneda"
    )
    impuesto = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Impuesto en porcentaje (ej: 13.00 para 13%)"
    )
    propina_sugerida = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Propina sugerida en porcentaje"
    )

    # Configuración de sistema
    idioma = models.CharField(
        max_length=10,
        default='es',
        choices=[
            ('es', 'Español'),
            ('en', 'English'),
        ],
        help_text="Idioma del sistema"
    )
    zona_horaria = models.CharField(
        max_length=50,
        default='America/La_Paz',
        help_text="Zona horaria del sistema"
    )
    tema = models.CharField(
        max_length=20,
        default='oscuro',
        choices=[
            ('claro', 'Claro'),
            ('oscuro', 'Oscuro'),
        ],
        help_text="Tema visual del sistema"
    )

    # Configuración de horarios
    hora_apertura = models.TimeField(
        default='08:00:00',
        help_text="Hora de apertura del restaurante"
    )
    hora_cierre = models.TimeField(
        default='22:00:00',
        help_text="Hora de cierre del restaurante"
    )

    # Configuración de reservas
    reserva_max_minutos = models.IntegerField(
        default=120,
        validators=[MinValueValidator(30)],
        help_text="Duración máxima de una reserva en minutos"
    )
    reserva_tolerancia_minutos = models.IntegerField(
        default=15,
        validators=[MinValueValidator(5)],
        help_text="Tolerancia en minutos antes de marcar no-show"
    )

    # Configuración de tickets/facturas
    ticket_footer = models.TextField(
        blank=True,
        null=True,
        help_text="Texto al pie del ticket (mensaje de agradecimiento, redes sociales, etc.)"
    )

    # Metadata
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración del Sistema"
        verbose_name_plural = "Configuración del Sistema"

    def __str__(self):
        return f"Configuración: {self.nombre}"

    def save(self, *args, **kwargs):
        """Garantiza que solo exista 1 configuración (Singleton)"""
        self.pk = 1  # Forzar siempre ID=1
        super().save(*args, **kwargs)

    @classmethod
    def get_configuracion(cls):
        """Obtiene la configuración única del sistema (o la crea si no existe)"""
        config, created = cls.objects.get_or_create(pk=1)
        if created:
            logger.info("Configuración del sistema creada por primera vez")
        return config

    def delete(self, *args, **kwargs):
        """Previene que se borre la configuración"""
        logger.warning("Intento de borrar ConfiguracionSistema bloqueado")
        pass  # No permitir borrado
