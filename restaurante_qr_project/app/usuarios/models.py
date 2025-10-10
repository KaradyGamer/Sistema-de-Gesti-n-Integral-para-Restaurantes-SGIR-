from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinLengthValidator, RegexValidator
import uuid

# Definir los roles como constante reutilizable
ROLES = [
    ('cliente', 'Cliente'),
    ('mesero', 'Mesero'),
    ('cocinero', 'Cocinero'),
    ('cajero', 'Cajero'),
    ('gerente', 'Gerente'),
    ('admin', 'Administrador'),
]

# Áreas disponibles en el sistema
AREAS_SISTEMA = [
    ('mesero', 'Área de Mesero'),
    ('cocina', 'Área de Cocina'),
    ('caja', 'Área de Caja'),
    ('reportes', 'Reportes'),
]

class Usuario(AbstractUser):
    rol = models.CharField(
        max_length=20,
        choices=ROLES,
        default='cliente'
    )

    # PIN para acceso rápido (SOLO para cajeros)
    pin = models.CharField(
        max_length=6,
        blank=True,
        null=True,
        unique=True,
        validators=[
            MinLengthValidator(4),
            RegexValidator(r'^\d+$', 'El PIN debe contener solo números.')
        ],
        help_text='PIN numérico de 4-6 dígitos - SOLO para cajeros'
    )

    # Token único para autenticación por QR
    qr_token = models.UUIDField(
        null=True,
        blank=True,
        editable=False,
        unique=True,
        help_text='Token único para autenticación vía QR'
    )

    # Permisos multi-área (para empleados que pueden acceder a múltiples áreas)
    areas_permitidas = models.JSONField(
        default=list,
        blank=True,
        help_text='Lista de áreas a las que tiene acceso el usuario'
    )

    # Control de estado del empleado
    activo = models.BooleanField(
        default=True,
        help_text='Si está desactivado, no puede iniciar sesión'
    )

    # Metadatos
    fecha_ultimo_qr = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Última vez que se generó un QR para este usuario'
    )

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_rol_display()})"

    def puede_usar_pin(self):
        """Verifica si el usuario puede usar PIN para login - SOLO CAJEROS"""
        return self.rol == 'cajero' and self.pin

    def puede_generar_qr(self):
        """Verifica si se puede generar QR para este usuario"""
        return self.rol in ['mesero', 'cocinero'] and self.activo

    def tiene_acceso_area(self, area):
        """Verifica si el usuario tiene acceso a un área específica"""
        if not self.areas_permitidas:
            # Si no tiene áreas configuradas, usar área por defecto según rol
            areas_default = {
                'mesero': ['mesero'],
                'cocinero': ['cocina'],
                'cajero': ['caja'],
                'gerente': ['mesero', 'cocina', 'caja', 'reportes'],
                'admin': ['mesero', 'cocina', 'caja', 'reportes'],
            }
            return area in areas_default.get(self.rol, [])
        return area in self.areas_permitidas

    def get_areas_activas(self):
        """Retorna lista de áreas a las que tiene acceso"""
        if not self.areas_permitidas:
            areas_default = {
                'mesero': ['mesero'],
                'cocinero': ['cocina'],
                'cajero': ['caja'],
                'gerente': ['mesero', 'cocina', 'caja', 'reportes'],
                'admin': ['mesero', 'cocina', 'caja', 'reportes'],
            }
            return areas_default.get(self.rol, [])
        return self.areas_permitidas

    def generar_qr_token(self):
        """Genera un nuevo token QR para el usuario"""
        from django.utils import timezone
        self.qr_token = uuid.uuid4()
        self.fecha_ultimo_qr = timezone.now()
        self.save()
        return self.qr_token

    def get_qr_token(self):
        """Retorna el token QR, generándolo si no existe"""
        if not self.qr_token:
            return self.generar_qr_token()
        return self.qr_token

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['first_name', 'last_name', 'username']
