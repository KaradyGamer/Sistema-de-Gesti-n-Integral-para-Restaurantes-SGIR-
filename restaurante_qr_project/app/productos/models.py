from django.db import models
from django.db.models import F
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal

class Categoria(models.Model):
    nombre = models.CharField(max_length=50)

    activo = models.BooleanField(default=True, help_text="Si False, la categoría está eliminada (soft delete)")
    fecha_eliminacion = models.DateTimeField(null=True, blank=True, help_text="Fecha en que se eliminó la categoría")
    eliminado_por = models.ForeignKey("usuarios.Usuario", on_delete=models.SET_NULL, null=True, blank=True, related_name="categorias_eliminadas")

    def __str__(self):
        return self.nombre

    def eliminar_suave(self, usuario=None):
        from django.utils import timezone
        self.activo = False
        self.fecha_eliminacion = timezone.now()
        self.eliminado_por = usuario
        self.save()

    def restaurar(self):
        self.activo = True
        self.fecha_eliminacion = None
        self.eliminado_por = None
        self.save()


class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    disponible = models.BooleanField(default=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True, related_name="productos")
    imagen = models.ImageField(upload_to="productos/", blank=True, null=True)
    stock_actual = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    stock_minimo = models.IntegerField(default=5, validators=[MinValueValidator(0)])
    requiere_inventario = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    fecha_eliminacion = models.DateTimeField(null=True, blank=True)
    eliminado_por = models.ForeignKey("usuarios.Usuario", on_delete=models.SET_NULL, null=True, blank=True, related_name="productos_eliminados")

    def __str__(self):
        return self.nombre

    def clean(self):
        super().clean()
        if self.precio is not None and self.precio <= 0:
            raise ValidationError({"precio": "El precio debe ser mayor a 0"})
        if self.stock_actual is not None and self.stock_actual < 0:
            raise ValidationError({"stock_actual": "El stock no puede ser negativo"})
    def save(self, *args, **kwargs):
        """
        Override save para ejecutar validaciones antes de guardar
        CRITICO: Asegura que nunca se guarden valores negativos
        """
        self.full_clean()
        super().save(*args, **kwargs)


    @property
    def stock_bajo(self):
        if self.requiere_inventario:
            return self.stock_actual <= self.stock_minimo
        return False

    @property
    def agotado(self):
        if self.requiere_inventario:
            return self.stock_actual <= 0
        return False

    def descontar_stock(self, cantidad):
        if not self.requiere_inventario:
            return True
        if cantidad <= 0:
            return False
        updated = Producto.objects.filter(id=self.id, stock_actual__gte=cantidad).update(stock_actual=F("stock_actual") - cantidad)
        if updated:
            self.refresh_from_db()
            if self.stock_bajo:
                self._crear_alerta_stock()
            return True
        return False

    def agregar_stock(self, cantidad):
        if cantidad <= 0:
            return False
        Producto.objects.filter(id=self.id).update(stock_actual=F("stock_actual") + cantidad)
        self.refresh_from_db()
        return True

    def _crear_alerta_stock(self):
        try:
            from app.caja.models import AlertaStock
            AlertaStock.objects.get_or_create(producto=self, tipo="stock_bajo" if self.stock_actual > 0 else "agotado", estado="activa", defaults={"stock_actual": self.stock_actual, "mensaje": f"{self.nombre} - Stock: {self.stock_actual}"})
        except:
            pass

    def eliminar_suave(self, usuario=None):
        from django.utils import timezone
        self.activo = False
        self.fecha_eliminacion = timezone.now()
        self.eliminado_por = usuario
        self.save()

    def restaurar(self):
        self.activo = True
        self.fecha_eliminacion = None
        self.eliminado_por = None
        self.save()
