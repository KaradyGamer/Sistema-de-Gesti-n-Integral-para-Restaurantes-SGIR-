"""
Modelos del módulo de Inventario.

Gestiona el control de stock de insumos y recetas de productos:
- Categorías de insumos (Carnes, Verduras, Lácteos, etc.)
- Insumos con stock mín/máx y alertas automáticas
- Movimientos de inventario (entradas/salidas) con auditoría
- Recetas de productos (ingredientes + cantidades)
- Integración con Pedidos para descuento automático de stock

IMPORTANTE: Los movimientos de stock deben registrarse en transacciones atómicas
para garantizar consistencia con los pedidos.
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class CategoriaInsumo(models.Model):
    """Categorías para clasificar insumos"""
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Categoría de Insumo"
        verbose_name_plural = "Categorías de Insumos"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Insumo(models.Model):
    """Insumos del inventario (ingredientes, materiales, etc.)"""

    UNIDADES = [
        ('kg', 'Kilogramo'),
        ('g', 'Gramo'),
        ('l', 'Litro'),
        ('ml', 'Mililitro'),
        ('unidad', 'Unidad'),
        ('paquete', 'Paquete'),
        ('caja', 'Caja'),
        ('bolsa', 'Bolsa'),
    ]

    categoria = models.ForeignKey(
        CategoriaInsumo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='insumos'
    )
    nombre = models.CharField(max_length=200)
    unidad = models.CharField(max_length=20, choices=UNIDADES, default='unidad')
    stock_actual = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Stock disponible actualmente"
    )
    stock_minimo = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Stock mínimo antes de generar alerta"
    )
    nota = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Insumo"
        verbose_name_plural = "Insumos"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.stock_actual} {self.unidad})"

    @property
    def stock_bajo(self):
        """Verifica si el stock está por debajo del mínimo"""
        return self.stock_actual <= self.stock_minimo and self.stock_actual > 0

    @property
    def agotado(self):
        """Verifica si el insumo está agotado"""
        return self.stock_actual == 0

    @property
    def estado_stock(self):
        """Devuelve el estado del stock como string"""
        if self.agotado:
            return 'agotado'
        elif self.stock_bajo:
            return 'bajo'
        else:
            return 'ok'

    def agregar_stock(self, cantidad, motivo="", usuario=None):
        """Agrega stock y registra el movimiento"""
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser positiva")

        self.stock_actual += cantidad
        self.save()

        # Registrar movimiento
        MovimientoInsumo.objects.create(
            insumo=self,
            tipo='entrada',
            cantidad=cantidad,
            motivo=motivo or "Entrada de stock",
            creado_por=usuario
        )

        logger.info(f"Stock agregado: {self.nombre} +{cantidad} {self.unidad}")
        return True

    def descontar_stock(self, cantidad, motivo="", usuario=None):
        """Descuenta stock y registra el movimiento"""
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser positiva")

        if self.stock_actual < cantidad:
            raise ValueError(f"Stock insuficiente. Disponible: {self.stock_actual} {self.unidad}")

        self.stock_actual -= cantidad
        self.save()

        # Registrar movimiento
        MovimientoInsumo.objects.create(
            insumo=self,
            tipo='salida',
            cantidad=cantidad,
            motivo=motivo or "Salida de stock",
            creado_por=usuario
        )

        # Generar alerta si queda bajo
        if self.stock_bajo or self.agotado:
            self._crear_alerta_stock()

        logger.info(f"Stock descontado: {self.nombre} -{cantidad} {self.unidad}")
        return True

    def ajustar_stock(self, cantidad_nueva, motivo="", usuario=None):
        """Ajusta el stock a un valor específico"""
        diferencia = cantidad_nueva - self.stock_actual
        self.stock_actual = cantidad_nueva
        self.save()

        # Registrar movimiento
        MovimientoInsumo.objects.create(
            insumo=self,
            tipo='ajuste',
            cantidad=diferencia,
            motivo=motivo or "Ajuste de inventario",
            creado_por=usuario
        )

        logger.info(f"Stock ajustado: {self.nombre} a {cantidad_nueva} {self.unidad}")
        return True

    def _crear_alerta_stock(self):
        """Crea una alerta de stock bajo/agotado"""
        # Reutilizar el modelo de AlertaStock de app.caja si existe
        try:
            from app.caja.models import AlertaStock

            if self.agotado:
                tipo_alerta = 'agotado'
                mensaje = f"Insumo agotado: {self.nombre}"
            else:
                tipo_alerta = 'bajo'
                mensaje = f"Stock bajo: {self.nombre} ({self.stock_actual}/{self.stock_minimo} {self.unidad})"

            # Crear alerta solo si no existe una reciente del mismo tipo
            AlertaStock.objects.get_or_create(
                # producto=None,  # No es producto, es insumo
                tipo=tipo_alerta,
                mensaje=mensaje,
                resuelta=False
            )

        except ImportError:
            logger.warning("No se pudo crear alerta de stock (modelo AlertaStock no disponible)")


class MovimientoInsumo(models.Model):
    """Historial de movimientos de insumos (entradas, salidas, ajustes)"""

    TIPOS = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
        ('ajuste', 'Ajuste'),
    ]

    insumo = models.ForeignKey(
        Insumo,
        on_delete=models.CASCADE,
        related_name='movimientos'
    )
    tipo = models.CharField(max_length=10, choices=TIPOS)
    cantidad = models.IntegerField(
        help_text="Cantidad movida (positiva para entrada, puede ser negativa para salida)"
    )
    motivo = models.TextField(help_text="Razón del movimiento")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimientos_insumos'
    )

    class Meta:
        verbose_name = "Movimiento de Insumo"
        verbose_name_plural = "Movimientos de Insumos"
        ordering = ['-fecha_creacion']

    def __str__(self):
        signo = '+' if self.tipo == 'entrada' else ('-' if self.tipo == 'salida' else '±')
        return f"{self.insumo.nombre} {signo}{abs(self.cantidad)} ({self.get_tipo_display()})"
