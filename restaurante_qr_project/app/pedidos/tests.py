from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal

from app.usuarios.models import Usuario
from app.mesas.models import Mesa
from app.productos.models import Producto, Categoria
from .models import Pedido, DetallePedido


class PedidoModelTestCase(TestCase):
    """Tests para el modelo Pedido"""

    def setUp(self):
        """Configurar datos de prueba"""
        # Crear usuario de prueba
        self.usuario = Usuario.objects.create_user(
            username='testuser',
            password='testpass123',
            rol='mesero'
        )

        # Crear mesa de prueba
        self.mesa = Mesa.objects.create(
            numero=1,
            estado='disponible',
            capacidad=4
        )

        # Crear categoría y productos de prueba
        self.categoria = Categoria.objects.create(nombre='Bebidas')
        self.producto1 = Producto.objects.create(
            nombre='Coca Cola',
            precio=Decimal('5.00'),
            categoria=self.categoria,
            disponible=True
        )
        self.producto2 = Producto.objects.create(
            nombre='Hamburguesa',
            precio=Decimal('25.00'),
            categoria=self.categoria,
            disponible=True
        )

    def test_crear_pedido(self):
        """Test: Crear un pedido básico"""
        pedido = Pedido.objects.create(
            mesa=self.mesa,
            fecha=timezone.now(),
            forma_pago='efectivo',
            estado=Pedido.ESTADO_CREADO,
            total=Decimal('30.00')
        )
        self.assertEqual(pedido.mesa.numero, 1)
        self.assertEqual(pedido.estado, Pedido.ESTADO_CREADO)
        self.assertEqual(pedido.total, Decimal('30.00'))

    def test_crear_detalle_pedido(self):
        """Test: Crear detalles de pedido"""
        pedido = Pedido.objects.create(
            mesa=self.mesa,
            fecha=timezone.now(),
            forma_pago='efectivo',
            estado=Pedido.ESTADO_CREADO,
            total=Decimal('30.00')
        )

        detalle = DetallePedido.objects.create(
            pedido=pedido,
            producto=self.producto1,
            cantidad=2,
            subtotal=Decimal('10.00')
        )

        self.assertEqual(detalle.cantidad, 2)
        self.assertEqual(detalle.subtotal, Decimal('10.00'))
        self.assertEqual(pedido.detalles.count(), 1)

    def test_calcular_total_pedido(self):
        """Test: Calcular el total de un pedido correctamente"""
        pedido = Pedido.objects.create(
            mesa=self.mesa,
            fecha=timezone.now(),
            forma_pago='efectivo',
            estado=Pedido.ESTADO_CREADO
        )

        # Agregar detalles
        DetallePedido.objects.create(
            pedido=pedido,
            producto=self.producto1,
            cantidad=2,
            subtotal=self.producto1.precio * 2
        )
        DetallePedido.objects.create(
            pedido=pedido,
            producto=self.producto2,
            cantidad=1,
            subtotal=self.producto2.precio * 1
        )

        # Calcular total esperado
        total_esperado = (self.producto1.precio * 2) + (self.producto2.precio * 1)
        pedido.total = total_esperado
        pedido.save()

        self.assertEqual(pedido.total, Decimal('35.00'))

    def test_cambiar_estado_pedido(self):
        """Test: Cambiar estados de pedido"""
        pedido = Pedido.objects.create(
            mesa=self.mesa,
            fecha=timezone.now(),
            forma_pago='efectivo',
            estado=Pedido.ESTADO_CREADO,
            total=Decimal('30.00')
        )

        # Cambiar a en preparación
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


class PedidoAPITestCase(TestCase):
    """Tests para las APIs de pedidos"""

    def setUp(self):
        """Configurar cliente y datos de prueba"""
        self.client = Client()

        # Crear usuario de prueba
        self.usuario = Usuario.objects.create_user(
            username='testuser',
            password='testpass123',
            rol='cocinero'
        )

        # Crear mesa
        self.mesa = Mesa.objects.create(
            numero=1,
            estado='disponible',
            capacidad=4
        )

        # Crear productos
        self.categoria = Categoria.objects.create(nombre='Comida')
        self.producto = Producto.objects.create(
            nombre='Pizza',
            precio=Decimal('40.00'),
            categoria=self.categoria,
            disponible=True
        )

    def test_crear_pedido_cliente_api(self):
        """Test: API de creación de pedidos cliente está DESHABILITADA por seguridad"""
        url = reverse('crear_pedido_deshabilitado')  # API deshabilitada desde 2026-01-04
        data = {
            'mesa_id': self.mesa.numero,
            'productos': [
                {
                    'producto_id': self.producto.id,
                    'cantidad': 2
                }
            ],
            'forma_pago': 'efectivo',
            'total': 80.00
        }

        # Verificar que la API está deshabilitada (404 Not Found)
        response = self.client.post(
            url,
            data=data,
            content_type='application/json'
        )

        # La API debe devolver 404 o 403 para prevenir spam/DoS
        self.assertIn(response.status_code, [403, 404])

        # Verificar que NO se creó ningún pedido
        pedido = Pedido.objects.filter(mesa=self.mesa).first()
        self.assertIsNone(pedido)

    def test_actualizar_estado_pedido_autenticado(self):
        """Test: Actualizar estado de pedido requiere autenticación"""
        # Crear un pedido
        pedido = Pedido.objects.create(
            mesa=self.mesa,
            fecha=timezone.now(),
            forma_pago='efectivo',
            estado=Pedido.ESTADO_CREADO,
            total=Decimal('40.00')
        )

        # Intentar actualizar sin autenticación
        url = reverse('actualizar_estado_pedido', args=[pedido.id])
        response = self.client.patch(
            url,
            data={'estado': Pedido.ESTADO_EN_PREPARACION},
            content_type='application/json'
        )

        # Debe redirigir o devolver 403
        self.assertIn(response.status_code, [302, 403])


class PedidoValidacionTestCase(TestCase):
    """Tests para validaciones de pedidos"""

    def setUp(self):
        """Configurar datos de prueba"""
        self.mesa = Mesa.objects.create(numero=1, capacidad=4)
        self.categoria = Categoria.objects.create(nombre='Bebidas')
        self.producto = Producto.objects.create(
            nombre='Jugo',
            precio=Decimal('8.00'),
            categoria=self.categoria,
            disponible=True
        )

    def test_pedido_sin_mesa_falla(self):
        """Test: No se puede crear pedido sin mesa"""
        with self.assertRaises(Exception):
            Pedido.objects.create(
                mesa=None,  # Sin mesa
                fecha=timezone.now(),
                forma_pago='efectivo',
                estado=Pedido.ESTADO_CREADO
            )

    def test_detalle_sin_cantidad_falla(self):
        """Test: Detalle de pedido requiere cantidad"""
        pedido = Pedido.objects.create(
            mesa=self.mesa,
            fecha=timezone.now(),
            forma_pago='efectivo',
            estado=Pedido.ESTADO_CREADO,
            total=Decimal('0.00')
        )

        # Intentar crear detalle sin cantidad
        with self.assertRaises(Exception):
            DetallePedido.objects.create(
                pedido=pedido,
                producto=self.producto,
                cantidad=None,  # Sin cantidad
                subtotal=Decimal('8.00')
            )


class PedidoIntegracionTestCase(TestCase):
    """Tests de integración para flujo completo de pedidos"""

    def setUp(self):
        """Configurar escenario completo"""
        self.usuario = Usuario.objects.create_user(
            username='cocinero1',
            password='pass123',
            rol='cocinero'
        )
        self.mesa = Mesa.objects.create(numero=5, capacidad=4)
        self.categoria = Categoria.objects.create(nombre='Platos')
        self.producto = Producto.objects.create(
            nombre='Pollo al horno',
            precio=Decimal('35.00'),
            categoria=self.categoria,
            disponible=True
        )

    def test_flujo_completo_pedido(self):
        """Test: Flujo completo desde creación hasta entrega"""
        # 1. Crear pedido
        pedido = Pedido.objects.create(
            mesa=self.mesa,
            fecha=timezone.now(),
            forma_pago='efectivo',
            estado=Pedido.ESTADO_CREADO
        )
        self.assertEqual(pedido.estado, Pedido.ESTADO_CREADO)

        # 2. Agregar productos
        DetallePedido.objects.create(
            pedido=pedido,
            producto=self.producto,
            cantidad=2,
            subtotal=self.producto.precio * 2
        )
        pedido.total = self.producto.precio * 2
        pedido.save()
        self.assertEqual(pedido.total, Decimal('70.00'))

        # 3. Cambiar a en preparación
        pedido.estado = Pedido.ESTADO_EN_PREPARACION
        pedido.save()
        self.assertEqual(pedido.estado, Pedido.ESTADO_EN_PREPARACION)

        # 4. Cambiar a listo
        pedido.estado = Pedido.ESTADO_LISTO
        pedido.save()
        self.assertEqual(pedido.estado, Pedido.ESTADO_LISTO)

        # 5. Entregar
        pedido.estado = Pedido.ESTADO_ENTREGADO
        pedido.save()
        self.assertEqual(pedido.estado, Pedido.ESTADO_ENTREGADO)

        # Verificar que el pedido tiene todos los datos correctos
        self.assertEqual(pedido.detalles.count(), 1)
        self.assertEqual(pedido.mesa.numero, 5)


class PedidoMaquinaEstadosTestCase(TestCase):
    """Tests para máquina de estados estricta"""

    def test_transiciones_validas_definidas(self):
        """Verifica que TRANSICIONES_VALIDAS esté definido"""
        self.assertIsNotNone(Pedido.TRANSICIONES_VALIDAS)
        self.assertIn(Pedido.ESTADO_CREADO, Pedido.TRANSICIONES_VALIDAS)

    def test_estados_terminales_sin_transiciones(self):
        """Verifica que estados terminales no permitan transiciones"""
        self.assertEqual(Pedido.TRANSICIONES_VALIDAS[Pedido.ESTADO_CANCELADO], [])
        self.assertEqual(Pedido.TRANSICIONES_VALIDAS[Pedido.ESTADO_CERRADO], [])

    def test_transicion_creado_a_confirmado_valida(self):
        """Verifica que creado -> confirmado es válido"""
        self.assertIn(Pedido.ESTADO_CONFIRMADO, Pedido.TRANSICIONES_VALIDAS[Pedido.ESTADO_CREADO])

    def test_transicion_cerrado_a_cancelado_invalida(self):
        """Verifica que NO se puede cancelar un pedido cerrado"""
        self.assertNotIn(Pedido.ESTADO_CANCELADO, Pedido.TRANSICIONES_VALIDAS[Pedido.ESTADO_CERRADO])

    def test_metodo_puede_cambiar_a_estado(self):
        """Verifica que el método puede_cambiar_a_estado funciona"""
        mesa = Mesa.objects.create(numero=1, capacidad=4)
        pedido = Pedido.objects.create(
            mesa=mesa,
            fecha=timezone.now(),
            estado=Pedido.ESTADO_CREADO
        )

        # Transición válida
        self.assertTrue(pedido.puede_cambiar_a_estado(Pedido.ESTADO_CONFIRMADO))

        # Transición inválida (no se puede ir directo a cerrado desde creado)
        self.assertFalse(pedido.puede_cambiar_a_estado(Pedido.ESTADO_CERRADO))


class PedidoTransaccionAtomicaTestCase(TestCase):
    """Tests para verificar transacciones atómicas"""

    def test_metodo_confirmar_tiene_transaction_atomic(self):
        """Verifica que confirmar() tiene decorator @transaction.atomic"""
        import inspect
        confirmar_source = inspect.getsource(Pedido.confirmar)
        self.assertIn('transaction.atomic', confirmar_source)

    def test_metodo_registrar_pago_tiene_transaction_atomic(self):
        """Verifica que registrar_pago() tiene decorator @transaction.atomic"""
        import inspect
        registrar_pago_source = inspect.getsource(Pedido.registrar_pago)
        self.assertIn('transaction.atomic', registrar_pago_source)

    def test_metodo_cerrar_pedido_tiene_transaction_atomic(self):
        """Verifica que cerrar_pedido() tiene decorator @transaction.atomic"""
        import inspect
        cerrar_pedido_source = inspect.getsource(Pedido.cerrar_pedido)
        self.assertIn('transaction.atomic', cerrar_pedido_source)
