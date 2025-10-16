from django.db import models
from django.db.models import F

class Categoria(models.Model):
    nombre = models.CharField(max_length=50)

    # ✅ NUEVO: Campos para eliminación suave (soft delete)
    activo = models.BooleanField(default=True, help_text='Si False, la categoría está eliminada (soft delete)')
    fecha_eliminacion = models.DateTimeField(null=True, blank=True, help_text='Fecha en que se eliminó la categoría')
    eliminado_por = models.ForeignKey('usuarios.Usuario', on_delete=models.SET_NULL, null=True, blank=True, related_name='categorias_eliminadas')

    def __str__(self):
        return self.nombre

    def eliminar_suave(self, usuario=None):
        """
        Eliminación suave: Marca la categoría como inactiva.
        Los productos históricos mantendrán la referencia.

        Args:
            usuario: Usuario que realizó la eliminación (opcional)
        """
        from django.utils import timezone
        self.activo = False
        self.fecha_eliminacion = timezone.now()
        self.eliminado_por = usuario
        self.save()

    def restaurar(self):
        """Restaura una categoría eliminada suavemente"""
        self.activo = True
        self.fecha_eliminacion = None
        self.eliminado_por = None
        self.save()


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

    # ✅ NUEVO: Campos para eliminación suave (soft delete)
    activo = models.BooleanField(default=True, help_text='Si False, el producto está eliminado (soft delete)')
    fecha_eliminacion = models.DateTimeField(null=True, blank=True, help_text='Fecha en que se eliminó el producto')
    eliminado_por = models.ForeignKey('usuarios.Usuario', on_delete=models.SET_NULL, null=True, blank=True, related_name='productos_eliminados')

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
        """
        Descuenta del stock al vender de forma ATÓMICA
        ✅ CORREGIDO: Evita race conditions usando F() expression
        """
        if not self.requiere_inventario:
            return True  # No requiere control de inventario

        # ✅ Actualización atómica - solo actualiza si hay suficiente stock
        updated = Producto.objects.filter(
            id=self.id,
            stock_actual__gte=cantidad  # Solo si stock actual >= cantidad
        ).update(stock_actual=F('stock_actual') - cantidad)

        if updated:
            # Refrescar el objeto para tener el stock actualizado
            self.refresh_from_db()

            # Verificar si llegó a stock bajo para crear alerta
            if self.stock_bajo:
                self._crear_alerta_stock()

            return True

        # No había suficiente stock
        return False

    def agregar_stock(self, cantidad):
        """
        Agrega stock (para reposiciones) de forma ATÓMICA
        ✅ CORREGIDO: Usa F() expression para evitar race conditions
        """
        # ✅ Actualización atómica
        Producto.objects.filter(id=self.id).update(
            stock_actual=F('stock_actual') + cantidad
        )
        self.refresh_from_db()

    def _crear_alerta_stock(self):
        """Crea alerta de stock bajo si no existe ya"""
        try:
            from app.caja.models import AlertaStock
            AlertaStock.objects.get_or_create(
                producto=self,
                tipo='stock_bajo' if self.stock_actual > 0 else 'agotado',
                estado='activa',
                defaults={
                    'stock_actual': self.stock_actual,
                    'mensaje': f'{self.nombre} - Stock: {self.stock_actual}'
                }
            )
        except Exception:
            pass  # No fallar si no existe el modelo AlertaStock

    def eliminar_suave(self, usuario=None):
        """
        Eliminación suave: Marca el producto como inactivo en lugar de eliminarlo.
        Los pedidos históricos mantendrán la referencia.

        Args:
            usuario: Usuario que realizó la eliminación (opcional)
        """
        from django.utils import timezone
        self.activo = False
        self.fecha_eliminacion = timezone.now()
        self.eliminado_por = usuario
        self.save()

    def restaurar(self):
        """Restaura un producto eliminado suavemente"""
        self.activo = True
        self.fecha_eliminacion = None
        self.eliminado_por = None
        self.save()
