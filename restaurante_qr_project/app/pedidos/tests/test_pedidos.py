"""
Tests para creación de pedidos y gestión de stock
"""
from django.test import TestCase
from decimal import Decimal
from app.pedidos.models import Pedido, DetallePedido
from app.productos.models import Producto, Categoria
from app.mesas.models import Mesa


class PedidoCreationTestCase(TestCase):
    """Tests para creación de pedidos"""

    def setUp(self):
        # Crear datos de prueba
        self.categoria = Categoria.objects.create(nombre='Bebidas', activo=True)
        self.producto = Producto.objects.create(
            nombre='Coca Cola',
            categoria=self.categoria,
            precio=Decimal('5.00'),
            disponible=True,
            requiere_inventario=True,
            stock_actual=50,
            stock_minimo=10,
            activo=True
        )
        self.mesa = Mesa.objects.create(
            numero=1,
            capacidad=4,
            estado='disponible',
            disponible=True,
            activo=True
        )

    def test_crear_pedido_stock_suficiente(self):
        """✅ Crear pedido con stock suficiente"""
        # Crear pedido
        pedido = Pedido.objects.create(
            mesa=self.mesa,
            estado=Pedido.ESTADO_CREADO
        )

        # Agregar detalle
        detalle = DetallePedido.objects.create(
            pedido=pedido,
            producto=self.producto,
            cantidad=2,
            precio_unitario=self.producto.precio
        )

        # Descontar stock
        self.assertTrue(self.producto.descontar_stock(2))

        # Verificar descuento
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock_actual, 48)

        # Verificar pedido
        self.assertEqual(pedido.estado, Pedido.ESTADO_CREADO)
        self.assertEqual(pedido.detalles.count(), 1)

    def test_crear_pedido_stock_insuficiente(self):
        """❌ Rechazar pedido sin stock suficiente"""
        # Intentar descontar más del stock disponible
        resultado = self.producto.descontar_stock(100)

        self.assertFalse(resultado)

        # Verificar que el stock NO se modificó
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock_actual, 50)

    def test_crear_pedido_producto_sin_inventario(self):
        """✅ Permitir pedido de producto sin control de inventario"""
        # Producto sin inventario
        producto_servicio = Producto.objects.create(
            nombre='Atención al Cliente',
            categoria=self.categoria,
            precio=Decimal('0.00'),
            disponible=True,
            requiere_inventario=False,
            activo=True
        )

        # Crear pedido
        pedido = Pedido.objects.create(mesa=self.mesa, estado=Pedido.ESTADO_CREADO)
        DetallePedido.objects.create(
            pedido=pedido,
            producto=producto_servicio,
            cantidad=1,
            precio_unitario=producto_servicio.precio
        )

        # Verificar creación exitosa
        self.assertEqual(pedido.detalles.count(), 1)

    def test_alerta_stock_bajo(self):
        """🔔 Generar alerta cuando stock baja del mínimo"""
        # Descontar hasta llegar a stock bajo
        self.producto.descontar_stock(41)  # Quedan 9 (menos del mínimo de 10)

        self.producto.refresh_from_db()
        self.assertTrue(self.producto.stock_bajo)
        self.assertEqual(self.producto.stock_actual, 9)

    def test_pedido_con_mesa_invalida(self):
        """❌ No permitir pedido con mesa inexistente"""
        with self.assertRaises(Exception):
            Pedido.objects.create(
                mesa_id=9999,  # Mesa inexistente
                estado=Pedido.ESTADO_CREADO
            )


class PedidoEstadosTestCase(TestCase):
    """Tests para cambios de estado de pedidos"""

    def setUp(self):
        self.categoria = Categoria.objects.create(nombre='Comidas', activo=True)
        self.producto = Producto.objects.create(
            nombre='Hamburguesa',
            categoria=self.categoria,
            precio=Decimal('25.00'),
            disponible=True,
            activo=True
        )
        self.mesa = Mesa.objects.create(numero=5, capacidad=4, activo=True)

    def test_flujo_completo_pedido(self):
        """✅ Flujo: pendiente → en_preparacion → listo → entregado"""
        # Crear pedido
        pedido = Pedido.objects.create(mesa=self.mesa, estado=Pedido.ESTADO_CREADO)
        DetallePedido.objects.create(
            pedido=pedido,
            producto=self.producto,
            cantidad=1,
            precio_unitario=self.producto.precio
        )

        # Cambiar a en_preparacion
        pedido.estado = Pedido.ESTADO_EN_PREPARACION
        pedido.save()
        self.assertEqual(pedido.estado, Pedido.ESTADO_EN_PREPARACION)

        # Cambiar a listo
        pedido.estado = Pedido.ESTADO_LISTO
        pedido.save()
        self.assertEqual(pedido.estado, Pedido.ESTADO_LISTO)

        # Cambiar a entregado
        pedido.estado = Pedido.ESTADO_ENTREGADO
        pedido.save()
        self.assertEqual(pedido.estado, Pedido.ESTADO_ENTREGADO)
