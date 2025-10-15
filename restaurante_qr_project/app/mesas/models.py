import qrcode
import os
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

    # Posición para mapa digital
    posicion_x = models.IntegerField(default=0, help_text='Posición X en el mapa')
    posicion_y = models.IntegerField(default=0, help_text='Posición Y en el mapa')

    def __str__(self):
        return f"Mesa {self.numero}"

    def save(self, *args, **kwargs):
        # Guardar primero para obtener el ID
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Generar QR solo si no existe o si es necesario actualizar
        if is_new or not self.qr_image:
            # Usar dominio desde settings o variable de entorno en producción
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
            buffer.seek(0)  # ✅ AGREGADO: Volver al inicio del buffer
            file_name = f"mesa-{self.numero}-qr.png"

            # ✅ CORREGIDO: Guardar sin llamar a save() recursivamente
            self.qr_image.save(file_name, File(buffer), save=False)
            # ✅ CORREGIDO: Actualizar solo el nombre del archivo, no el objeto
            Mesa.objects.filter(pk=self.pk).update(qr_image=self.qr_image.name)
