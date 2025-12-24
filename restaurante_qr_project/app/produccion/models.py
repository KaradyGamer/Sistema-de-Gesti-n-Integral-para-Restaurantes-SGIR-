"""
SGIR v40.5.0 - Módulo de Producción y Recetario
Gestiona fabricación de productos y consumo de insumos
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal


class Receta(models.Model):
    """
    Receta maestra para productos fabricables.
    Define qué insumos se necesitan para fabricar 1 unidad del producto.
    """
    producto = models.OneToOneField(
        'productos.Producto',
        on_delete=models.PROTECT,
        related_name='receta',
        help_text='Producto que se fabrica con esta receta'
    )
    activo = models.BooleanField(default=True)
    version = models.IntegerField(default=1, help_text='Versión de la receta')
    creado_por = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recetas_creadas'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Receta'
        verbose_name_plural = 'Recetas'
        ordering = ['producto__nombre']

    def __str__(self):
        return f"Receta {self.producto.nombre} v{self.version}"

    def clean(self):
        super().clean()
        if self.producto and not getattr(self.producto, 'es_fabricable', False):
            raise ValidationError({
                'producto': 'El producto debe tener es_fabricable=True para poder crear una receta'
            })


class RecetaItem(models.Model):
    """
    Insumo individual requerido en una receta.
    Cantidad es por 1 unidad de producto fabricado.
    """
    receta = models.ForeignKey(
        Receta,
        on_delete=models.CASCADE,
        related_name='items'
    )
    insumo = models.ForeignKey(
        'inventario.Insumo',
        on_delete=models.PROTECT,
        related_name='recetas_que_lo_usan'
    )
    cantidad = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))],
        help_text='Cantidad de insumo por 1 unidad de producto'
    )
    merma_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Porcentaje de merma (ej: 5.00 = 5%)'
    )

    class Meta:
        verbose_name = 'Ítem de Receta'
        verbose_name_plural = 'Ítems de Receta'
        unique_together = [['receta', 'insumo']]
        ordering = ['insumo__nombre']

    def __str__(self):
        return f"{self.insumo.nombre}: {self.cantidad} {self.insumo.unidad}"

    def clean(self):
        super().clean()
        if self.cantidad <= 0:
            raise ValidationError({'cantidad': 'La cantidad debe ser mayor a 0'})
        if self.merma_pct < 0:
            raise ValidationError({'merma_pct': 'La merma no puede ser negativa'})

    @property
    def cantidad_con_merma(self):
        """Calcula cantidad incluyendo merma"""
        return self.cantidad * (1 + self.merma_pct / Decimal('100'))


class Produccion(models.Model):
    """
    Registro de fabricación de productos.
    Estado: registrada -> aplicada -> anulada
    """
    ESTADOS = [
        ('registrada', 'Registrada'),
        ('aplicada', 'Aplicada'),
        ('anulada', 'Anulada'),
    ]

    producto = models.ForeignKey(
        'productos.Producto',
        on_delete=models.PROTECT,
        related_name='producciones'
    )
    receta = models.ForeignKey(
        Receta,
        on_delete=models.PROTECT,
        related_name='producciones',
        help_text='Receta utilizada en esta producción'
    )
    cantidad_producida = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))],
        help_text='Cantidad de producto fabricado'
    )
    lote = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Código de lote opcional'
    )
    estado = models.CharField(max_length=20, choices=ESTADOS, default='registrada')
    notas = models.TextField(blank=True, null=True)

    # Auditoría de creación
    creado_por = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        related_name='producciones_registradas'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    # Auditoría de aplicación
    aplicado_por = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='producciones_aplicadas'
    )
    fecha_aplicacion = models.DateTimeField(null=True, blank=True)

    # Auditoría de anulación
    motivo_anulacion = models.TextField(null=True, blank=True)
    anulado_por = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='producciones_anuladas'
    )
    fecha_anulacion = models.DateTimeField(null=True, blank=True)
    pin_secundario_validado = models.BooleanField(
        default=False,
        help_text='Marca si se validó PIN secundario para anular (NO guarda el PIN)'
    )

    class Meta:
        verbose_name = 'Producción'
        verbose_name_plural = 'Producciones'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['-fecha_creacion']),
            models.Index(fields=['producto', 'estado']),
            models.Index(fields=['lote']),
        ]

    def __str__(self):
        return f"Producción {self.producto.nombre} x{self.cantidad_producida} ({self.get_estado_display()})"

    def clean(self):
        super().clean()
        if self.cantidad_producida <= 0:
            raise ValidationError({'cantidad_producida': 'Debe producir al menos una unidad'})
        if self.producto and not getattr(self.producto, 'es_fabricable', False):
            raise ValidationError({'producto': 'Solo productos fabricables pueden ser producidos'})


class ProduccionDetalle(models.Model):
    """
    Snapshot de consumo de insumo en una producción específica.
    Registra stock antes/después para auditoría completa.
    """
    produccion = models.ForeignKey(
        Produccion,
        on_delete=models.CASCADE,
        related_name='detalles'
    )
    insumo = models.ForeignKey(
        'inventario.Insumo',
        on_delete=models.PROTECT,
        related_name='producciones_detalle'
    )
    cantidad_calculada = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        help_text='Cantidad consumida (receta * cantidad_producida + merma)'
    )
    unidad_snapshot = models.CharField(
        max_length=20,
        help_text='Unidad del insumo al momento de la producción'
    )
    stock_insumo_antes = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        help_text='Stock del insumo antes de aplicar'
    )
    stock_insumo_despues = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        help_text='Stock del insumo después de aplicar'
    )

    class Meta:
        verbose_name = 'Detalle de Producción'
        verbose_name_plural = 'Detalles de Producción'
        unique_together = [['produccion', 'insumo']]
        ordering = ['insumo__nombre']

    def __str__(self):
        return f"{self.insumo.nombre}: {self.cantidad_calculada} {self.unidad_snapshot}"