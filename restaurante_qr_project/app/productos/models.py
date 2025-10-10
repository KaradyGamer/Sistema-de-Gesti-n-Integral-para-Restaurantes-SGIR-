from django.db import models

class Categoria(models.Model):
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    disponible = models.BooleanField(default=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True, related_name='productos')
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)

    # Campos nuevos para control de inventario
    stock_actual = models.IntegerField(default=0, help_text='Cantidad disponible en inventario')
    stock_minimo = models.IntegerField(default=5, help_text='Stock mínimo antes de alerta')
    requiere_inventario = models.BooleanField(default=False, help_text='Si requiere control de stock')

    def __str__(self):
        return self.nombre

    @property
    def stock_bajo(self):
        """Verifica si el stock está por debajo del mínimo"""
        if self.requiere_inventario:
            return self.stock_actual <= self.stock_minimo
        return False

    @property
    def agotado(self):
        """Verifica si el producto está agotado"""
        if self.requiere_inventario:
            return self.stock_actual <= 0
        return False

    def descontar_stock(self, cantidad):
        """Descuenta del stock al vender"""
        if self.requiere_inventario and self.stock_actual >= cantidad:
            self.stock_actual -= cantidad
            self.save()
            return True
        return False

    def agregar_stock(self, cantidad):
        """Agrega stock (para reposiciones)"""
        self.stock_actual += cantidad
        self.save()
