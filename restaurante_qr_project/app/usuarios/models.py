from django.contrib.auth.models import AbstractUser
from django.contrib.auth.hashers import make_password, check_password
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

    # PIN para acceso rápido (SOLO para cajeros) - DEPRECADO: usar pin_caja_hash
    pin = models.CharField(
        max_length=6,
        blank=True,
        null=True,
        unique=True,
        validators=[
            MinLengthValidator(4),
            RegexValidator(r'^\d+$', 'El PIN debe contener solo números.')
        ],
        help_text='DEPRECADO: PIN numérico de 4-6 dígitos - usar pin_caja_hash'
    )

    # PIN caja hasheado (para operaciones normales de cajero)
    pin_caja_hash = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        help_text='Hash del PIN de caja (PBKDF2) - NUNCA guardar texto plano'
    )

    # PIN secundario hasheado (para operaciones sensibles)
    pin_secundario_hash = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        help_text='Hash del PIN secundario para operaciones sensibles (anular producción, cerrar con deuda)'
    )

    # PIN secundario en texto plano - DEPRECADO: usar pin_secundario_hash
    pin_secundario = models.CharField(
        max_length=6,
        blank=True,
        null=True,
        validators=[
            MinLengthValidator(4),
            RegexValidator(r'^\d+$', 'El PIN secundario debe contener solo números.')
        ],
        help_text='DEPRECADO: usar pin_secundario_hash'
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
        return f"{self.get_full_name() or self.username} ({self.get_rol_display()})"

    def set_pin_caja(self, pin_texto):
        """
        Establece el PIN de caja hasheado.

        Args:
            pin_texto: str, PIN de 4-6 dígitos numérico

        Raises:
            ValueError: Si el PIN no cumple formato
        """
        import re
        if not pin_texto:
            raise ValueError("El PIN no puede estar vacío")
        if not re.match(r'^\d{4,6}$', str(pin_texto)):
            raise ValueError("El PIN debe tener 4-6 dígitos numéricos")

        self.pin_caja_hash = make_password(str(pin_texto))
        # NO guardar en pin (campo deprecado)

    def validar_pin_caja(self, pin_ingresado):
        """
        Valida el PIN de caja contra el hash almacenado.

        Args:
            pin_ingresado: str, PIN a validar

        Returns:
            bool: True si el PIN es correcto
        """
        if not self.pin_caja_hash:
            # Fallback legacy: verificar pin deprecado
            if self.pin:
                return str(pin_ingresado) == str(self.pin)
            return False
        return check_password(str(pin_ingresado), self.pin_caja_hash)

    def set_pin_secundario(self, pin_texto):
        """
        Establece el PIN secundario hasheado.

        Args:
            pin_texto: str, PIN de 4-6 dígitos numérico

        Raises:
            ValueError: Si el PIN no cumple formato
        """
        import re
        if not pin_texto:
            raise ValueError("El PIN secundario no puede estar vacío")
        if not re.match(r'^\d{4,6}$', str(pin_texto)):
            raise ValueError("El PIN secundario debe tener 4-6 dígitos numéricos")

        self.pin_secundario_hash = make_password(str(pin_texto))
        # NO guardar en pin_secundario (campo deprecado)

    def validar_pin_secundario_hash(self, pin_ingresado):
        """
        Valida el PIN secundario contra el hash almacenado.

        Args:
            pin_ingresado: str, PIN a validar

        Returns:
            bool: True si el PIN es correcto
        """
        if not self.pin_secundario_hash:
            # Fallback legacy: verificar pin_secundario deprecado
            if self.pin_secundario:
                return str(pin_ingresado) == str(self.pin_secundario)
            return False
        return check_password(str(pin_ingresado), self.pin_secundario_hash)

    def puede_usar_pin(self):
        """Verifica si el usuario puede usar PIN para login - SOLO CAJEROS"""
        return self.rol == 'cajero' and (self.pin_caja_hash or self.pin)

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
        """Restaura un usuario desactivado"""
        self.activo = True
        self.is_active = True  # Reactivar login de Django
        self.fecha_eliminacion = None
        self.eliminado_por = None
        self.save()

    def validar_pin_secundario(self, pin_ingresado):
        """
        Valida el PIN secundario sin almacenarlo.
        DELEGADO a validar_pin_secundario_hash para compatibilidad.

        Args:
            pin_ingresado: str, PIN a validar

        Returns:
            bool: True si el PIN es correcto
        """
        return self.validar_pin_secundario_hash(pin_ingresado)

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['first_name', 'last_name', 'username']


class QRToken(models.Model):
    """
    Modelo para tokens QR regenerables
    Permite invalidar tokens anteriores al generar nuevos
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
        estado = 'Activo' if self.activo else 'Inactivo'
        return f"QR Token - {self.usuario.username} ({estado})"

    def esta_expirado(self):
        """✅ NUEVO: Verifica si el token está expirado"""
        from django.utils import timezone
        if not self.fecha_expiracion:
            return False  # Tokens antiguos sin expiración
        return timezone.now() > self.fecha_expiracion

    def invalidar(self):
        """Invalida este token"""
        from django.utils import timezone
        self.activo = False
        self.fecha_invalidacion = timezone.now()
        self.save()

    def marcar_usado(self):
        """✅ ACTUALIZADO: Marca el token como usado e inactivo"""
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
