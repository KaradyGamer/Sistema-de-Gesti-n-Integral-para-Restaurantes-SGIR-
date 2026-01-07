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
    """
    Modelo extendido de Usuario para el sistema de restaurante.

    Hereda de AbstractUser de Django y agrega campos específicos para:
    - Gestión de roles (cliente, mesero, cocinero, cajero, gerente, admin)
    - Autenticación mediante PIN (para cajeros)
    - Autenticación mediante QR (para meseros y cocineros)
    - Control de acceso multi-área
    - Eliminación suave (soft delete) para mantener integridad referencial
    """
    # Campo principal: Rol del usuario en el sistema
    rol = models.CharField(
        max_length=20,
        choices=ROLES,
        default='cliente',
        help_text='Rol que determina los permisos del usuario'
    )

    # PIN para acceso rápido (SOLO para cajeros)
    # Permite login rápido mediante código numérico de 4-6 dígitos
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
        help_text='Si está desactivado, no puede iniciar sesión (soft delete)'
    )

    # ✅ NUEVO: Campos adicionales para eliminación suave
    fecha_eliminacion = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Fecha en que se desactivó el usuario (soft delete)'
    )
    eliminado_por = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios_eliminados',
        help_text='Usuario que desactivó esta cuenta'
    )

    # Metadatos
    fecha_ultimo_qr = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Última vez que se generó un QR para este usuario'
    )

    def __str__(self):
        """Representación en texto del usuario mostrando nombre completo y rol"""
        return f"{self.get_full_name() or self.username} ({self.get_rol_display()})"

    def puede_usar_pin(self):
        """
        Verifica si el usuario puede usar PIN para login.

        Returns:
            bool: True si es cajero y tiene PIN configurado
        """
        return self.rol == 'cajero' and self.pin

    def puede_generar_qr(self):
        """
        Verifica si se puede generar código QR para este usuario.

        Returns:
            bool: True si es mesero o cocinero y está activo
        """
        return self.rol in ['mesero', 'cocinero'] and self.activo

    def tiene_acceso_area(self, area):
        """
        Verifica si el usuario tiene acceso a un área específica del sistema.

        Args:
            area: Nombre del área a verificar (mesero, cocina, caja, reportes)

        Returns:
            bool: True si el usuario tiene acceso al área especificada
        """
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
        """
        Retorna lista de áreas a las que el usuario tiene acceso.

        Returns:
            list: Lista de nombres de áreas según el rol o configuración personalizada
        """
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
        """
        Genera un nuevo token UUID para autenticación QR.

        Returns:
            UUID: Token único generado para el usuario
        """
        from django.utils import timezone
        self.qr_token = uuid.uuid4()
        self.fecha_ultimo_qr = timezone.now()
        self.save()
        return self.qr_token

    def get_qr_token(self):
        """
        Retorna el token QR del usuario, generándolo si no existe.

        Returns:
            UUID: Token QR del usuario
        """
        if not self.qr_token:
            return self.generar_qr_token()
        return self.qr_token

    def eliminar_suave(self, usuario_que_elimina=None):
        """
        Eliminación suave: Desactiva el usuario en lugar de eliminarlo.
        Los pedidos, transacciones y logs mantendrán la referencia.

        Args:
            usuario_que_elimina: Usuario que realizó la eliminación (opcional)
        """
        from django.utils import timezone
        self.activo = False
        self.is_active = False  # También desactivar login de Django
        self.fecha_eliminacion = timezone.now()
        self.eliminado_por = usuario_que_elimina
        self.save()

    def restaurar(self):
        """
        Restaura un usuario previamente desactivado.

        Reactiva el usuario y limpia los campos de eliminación.
        """
        self.activo = True
        self.is_active = True  # Reactivar login de Django
        self.fecha_eliminacion = None
        self.eliminado_por = None
        self.save()

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['first_name', 'last_name', 'username']


class QRToken(models.Model):
    """
    Modelo para tokens QR regenerables.

    Gestiona tokens únicos para autenticación mediante código QR.
    Permite invalidar tokens anteriores al generar nuevos, brindando
    mayor seguridad. Los tokens tienen fecha de expiración (24h por defecto).
    """
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='qr_tokens',
        help_text='Usuario al que pertenece este token'
    )

    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        help_text='Token único para autenticación vía QR'
    )

    ip_generacion = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP del servidor cuando se generó el QR'
    )

    activo = models.BooleanField(
        default=True,
        help_text='Si está activo, el token puede usarse para login'
    )

    usado = models.BooleanField(
        default=False,
        help_text='Si ya se usó para hacer login'
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        help_text='Fecha y hora de creación del token'
    )

    fecha_uso = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Fecha y hora en que se usó el token'
    )

    fecha_invalidacion = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Fecha y hora en que se invalidó el token'
    )

    # ✅ NUEVO: Fecha de expiración del token
    fecha_expiracion = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Fecha y hora de expiración del token (24h por defecto)'
    )

    class Meta:
        verbose_name = 'Token QR'
        verbose_name_plural = 'Tokens QR'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['token', 'activo', 'usado']),
            models.Index(fields=['usuario', 'activo']),
        ]

    def __str__(self):
        """Representación en texto del token QR con su estado"""
        estado = 'Activo' if self.activo else 'Inactivo'
        return f"QR Token - {self.usuario.username} ({estado})"

    def esta_expirado(self):
        """
        Verifica si el token ha excedido su fecha de expiración.

        Returns:
            bool: True si el token está expirado
        """
        from django.utils import timezone
        if not self.fecha_expiracion:
            return False  # Tokens antiguos sin expiración
        return timezone.now() > self.fecha_expiracion

    def invalidar(self):
        """
        Marca el token como inactivo.

        Usado cuando se genera un nuevo token o por seguridad.
        """
        from django.utils import timezone
        self.activo = False
        self.fecha_invalidacion = timezone.now()
        self.save()

    def marcar_usado(self):
        """
        Marca el token como usado y lo desactiva.

        Se ejecuta cuando el usuario inicia sesión con el QR.
        Desactiva automáticamente el token para evitar reutilización.
        """
        from django.utils import timezone
        self.usado = True
        self.activo = False  # ✅ Desactivar al usar
        self.fecha_uso = timezone.now()
        self.save()

    @classmethod
    def generar_token(cls, usuario, ip_actual, duracion_horas=24):
        """
        ✅ ACTUALIZADO: Genera un nuevo token para el usuario con expiración
        Invalida todos los tokens anteriores

        Args:
            usuario: Usuario para quien se genera el token
            ip_actual: IP desde donde se genera
            duracion_horas: Duración del token en horas (default: 24h)
        """
        from django.utils import timezone
        from datetime import timedelta

        # Invalidar todos los tokens anteriores del usuario
        cls.objects.filter(usuario=usuario, activo=True).update(
            activo=False,
            fecha_invalidacion=timezone.now()
        )

        # Crear nuevo token con expiración
        fecha_expiracion = timezone.now() + timedelta(hours=duracion_horas)
        nuevo_token = cls.objects.create(
            usuario=usuario,
            ip_generacion=ip_actual,
            fecha_expiracion=fecha_expiracion  # ✅ NUEVO
        )

        return nuevo_token
