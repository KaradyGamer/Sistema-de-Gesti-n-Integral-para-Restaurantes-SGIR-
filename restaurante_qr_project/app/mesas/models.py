import qrcode
from io import BytesIO
from django.core.files import File
from django.db import models
from django.conf import settings

class Mesa(models.Model):
    numero = models.PositiveIntegerField(unique=True)
    estado = models.CharField(
        max_length=20,
        choices=[
            ('disponible', 'Disponible'),
            ('ocupada', 'Ocupada'),
            ('reservada', 'Reservada'),
            ('pagando', 'Pagando'),  # Nuevo estado para caja
        ],
        default='disponible'
    )
    qr_image = models.ImageField(upload_to='qrcodes/', blank=True, null=True)

    # Campos nuevos para módulo de caja
    capacidad = models.PositiveIntegerField(default=4, help_text='Número de personas que caben en la mesa')
    disponible = models.BooleanField(default=True, help_text='Mesa activa para uso')

    # ✅ NUEVO: Sistema de unión de mesas
    es_combinada = models.BooleanField(default=False, help_text='Indica si está unida con otra mesa')
    mesas_combinadas = models.CharField(max_length=100, blank=True, null=True, help_text='IDs de mesas combinadas (ej: "1,2,3")')
    capacidad_combinada = models.PositiveIntegerField(default=0, help_text='Capacidad total cuando está combinada')

    # Posición para mapa digital
    posicion_x = models.IntegerField(default=0, help_text='Posición X en el mapa')
    posicion_y = models.IntegerField(default=0, help_text='Posición Y en el mapa')

    # ✅ NUEVO: Campos para eliminación suave (soft delete)
    activo = models.BooleanField(default=True, help_text='Si False, la mesa está eliminada (soft delete)')
    fecha_eliminacion = models.DateTimeField(null=True, blank=True, help_text='Fecha en que se eliminó la mesa')
    eliminado_por = models.ForeignKey('usuarios.Usuario', on_delete=models.SET_NULL, null=True, blank=True, related_name='mesas_eliminadas')

    def __str__(self):
        return f"Mesa {self.numero}"

    def save(self, *args, **kwargs):
        """
        ✅ OPTIMIZADO: Solo genera QR cuando es nueva mesa o fuerza regeneración (#5)
        """
        # ✅ Detectar si necesitamos generar QR
        generar_qr = False

        if self.pk is None:
            # Es una mesa nueva
            generar_qr = True
        elif not self.qr_image:
            # La mesa existe pero no tiene QR
            generar_qr = True
        elif kwargs.pop('force_qr_generation', False):
            # Regeneración forzada (opcional)
            generar_qr = True

        # Guardar primero para obtener el ID
        super().save(*args, **kwargs)

        # Solo generar QR si es necesario
        if generar_qr:
            self._generate_qr_code()

    def _generate_qr_code(self):
        """
        ✅ NUEVO: Método privado para generar QR sin llamar a save()
        Separado del save() principal para evitar regeneraciones innecesarias
        """
        from django.contrib.sites.models import Site

        try:
            domain = Site.objects.get_current().domain
            protocol = 'https' if settings.DEBUG is False else 'http'
        except:
            domain = '127.0.0.1:8000'
            protocol = 'http'

        url_qr = f"{protocol}://{domain}/menu/mesa/{self.id}/"
        qr = qrcode.make(url_qr)
        buffer = BytesIO()
        qr.save(buffer, format='PNG')
        buffer.seek(0)
        file_name = f"mesa-{self.numero}-qr.png"

        # Guardar sin llamar a save() recursivamente
        self.qr_image.save(file_name, File(buffer), save=False)

        # Actualizar solo el campo qr_image en la base de datos
        Mesa.objects.filter(pk=self.pk).update(qr_image=self.qr_image.name)

    def eliminar_suave(self, usuario=None):
        """
        Eliminación suave: Marca la mesa como inactiva en lugar de eliminarla.
        Las reservas y pedidos históricos mantendrán la referencia.

        Args:
            usuario: Usuario que realizó la eliminación (opcional)
        """
        from django.utils import timezone
        self.activo = False
        self.disponible = False  # También marcar como no disponible
        self.fecha_eliminacion = timezone.now()
        self.eliminado_por = usuario
        self.save()

    def restaurar(self):
        """Restaura una mesa eliminada suavemente"""
        self.activo = True
        self.disponible = True
        self.fecha_eliminacion = None
        self.eliminado_por = None
        self.save()
