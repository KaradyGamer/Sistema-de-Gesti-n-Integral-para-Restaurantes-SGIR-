"""
SGIR v40.5.1 - Tests mínimos para Producción
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal

from app.productos.models import Producto
from app.inventario.models import Insumo
from .models import Receta, RecetaItem, Produccion
from .services import (
    crear_receta,
    actualizar_receta,
    registrar_produccion,
    aplicar_produccion,
    anular_produccion
)

Usuario = get_user_model()


class RecetaTestCase(TestCase):
    """Tests para recetas"""

    def setUp(self):
        self.usuario = Usuario.objects.create_user(username='test_user', password='testpass')
        self.producto = Producto.objects.create(
            nombre='Pizza',
            precio=25.00,
            es_fabricable=True
        )
        self.insumo_harina = Insumo.objects.create(nombre='Harina', unidad='kg', stock_actual=100)
        self.insumo_tomate = Insumo.objects.create(nombre='Tomate', unidad='kg', stock_actual=50)

    def test_crear_receta_ok(self):
        """Test: crear receta correctamente"""
        items = [
            {'insumo_id': self.insumo_harina.id, 'cantidad': 0.5, 'merma_pct': 5},
            {'insumo_id': self.insumo_tomate.id, 'cantidad': 0.2, 'merma_pct': 0},
        ]

        receta = crear_receta(self.producto, items, self.usuario)

        self.assertIsNotNone(receta)
        self.assertEqual(receta.producto, self.producto)
        self.assertEqual(receta.items.count(), 2)
        self.assertEqual(receta.version, 1)

    def test_crear_receta_insumo_duplicado_falla(self):
        """Test: receta con insumo duplicado debe fallar"""
        items = [
            {'insumo_id': self.insumo_harina.id, 'cantidad': 0.5, 'merma_pct': 5},
            {'insumo_id': self.insumo_harina.id, 'cantidad': 0.3, 'merma_pct': 0},  # Duplicado
        ]

        with self.assertRaises(Exception):
            crear_receta(self.producto, items, self.usuario)


class ProduccionTestCase(TestCase):
    """Tests para producción"""

    def setUp(self):
        self.usuario = Usuario.objects.create_user(username='test_user', password='testpass')
        self.usuario.set_pin_secundario('1234')
        self.usuario.save()

        self.producto = Producto.objects.create(
            nombre='Pizza',
            precio=25.00,
            es_fabricable=True,
            requiere_inventario=True,
            stock_actual=0
        )
        self.insumo_harina = Insumo.objects.create(nombre='Harina', unidad='kg', stock_actual=100)
        self.insumo_tomate = Insumo.objects.create(nombre='Tomate', unidad='kg', stock_actual=50)

        items = [
            {'insumo_id': self.insumo_harina.id, 'cantidad': 0.5, 'merma_pct': 0},
            {'insumo_id': self.insumo_tomate.id, 'cantidad': 0.2, 'merma_pct': 0},
        ]
        self.receta = crear_receta(self.producto, items, self.usuario)

    def test_aplicar_produccion_ok(self):
        """Test: aplicar producción descuenta insumos y aumenta producto"""
        produccion = registrar_produccion(self.producto, Decimal('10'), 'LOTE-001', '', self.usuario)

        # Stock inicial
        stock_harina_antes = self.insumo_harina.stock_actual
        stock_tomate_antes = self.insumo_tomate.stock_actual
        stock_producto_antes = self.producto.stock_actual

        # Aplicar producción
        produccion = aplicar_produccion(produccion.id, self.usuario)

        # Refrescar
        self.insumo_harina.refresh_from_db()
        self.insumo_tomate.refresh_from_db()
        self.producto.refresh_from_db()

        # Verificar descuento de insumos
        self.assertEqual(self.insumo_harina.stock_actual, stock_harina_antes - 5)  # 0.5 * 10
        self.assertEqual(self.insumo_tomate.stock_actual, stock_tomate_antes - 2)  # 0.2 * 10

        # Verificar incremento de producto
        self.assertEqual(self.producto.stock_actual, stock_producto_antes + 10)

        # Verificar estado
        self.assertEqual(produccion.estado, 'aplicada')

    def test_aplicar_produccion_sin_stock_falla(self):
        """Test: aplicar producción sin stock debe hacer rollback"""
        # Reducir stock de tomate a 0
        self.insumo_tomate.stock_actual = 0
        self.insumo_tomate.save()

        produccion = registrar_produccion(self.producto, Decimal('10'), 'LOTE-002', '', self.usuario)

        # Stock inicial
        stock_harina_antes = self.insumo_harina.stock_actual
        stock_producto_antes = self.producto.stock_actual

        # Aplicar producción debe fallar
        with self.assertRaises(Exception):
            aplicar_produccion(produccion.id, self.usuario)

        # Refrescar
        self.insumo_harina.refresh_from_db()
        self.producto.refresh_from_db()

        # Verificar que NO se modificó NADA (rollback)
        self.assertEqual(self.insumo_harina.stock_actual, stock_harina_antes)
        self.assertEqual(self.producto.stock_actual, stock_producto_antes)

    def test_anular_produccion_sin_pin_falla(self):
        """Test: anular producción sin PIN secundario falla"""
        produccion = registrar_produccion(self.producto, Decimal('5'), 'LOTE-003', '', self.usuario)
        produccion = aplicar_produccion(produccion.id, self.usuario)

        with self.assertRaises(Exception):
            anular_produccion(produccion.id, 'Test', self.usuario, 'pin_incorrecto')

    def test_anular_produccion_con_pin_ok(self):
        """Test: anular producción con PIN correcto revierte todo"""
        produccion = registrar_produccion(self.producto, Decimal('5'), 'LOTE-004', '', self.usuario)

        # Stock antes
        stock_harina_antes = self.insumo_harina.stock_actual
        stock_tomate_antes = self.insumo_tomate.stock_actual
        stock_producto_antes = self.producto.stock_actual

        # Aplicar
        produccion = aplicar_produccion(produccion.id, self.usuario)

        # Anular con PIN correcto
        produccion = anular_produccion(produccion.id, 'Error en registro', self.usuario, '1234')

        # Refrescar
        self.insumo_harina.refresh_from_db()
        self.insumo_tomate.refresh_from_db()
        self.producto.refresh_from_db()

        # Verificar reversión completa
        self.assertEqual(self.insumo_harina.stock_actual, stock_harina_antes)
        self.assertEqual(self.insumo_tomate.stock_actual, stock_tomate_antes)
        self.assertEqual(self.producto.stock_actual, stock_producto_antes)
        self.assertEqual(produccion.estado, 'anulada')