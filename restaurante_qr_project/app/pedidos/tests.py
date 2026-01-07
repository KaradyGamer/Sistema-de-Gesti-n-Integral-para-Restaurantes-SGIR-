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
        pedido.estado = 'listo'
        pedido.save()
        self.assertEqual(pedido.estado, 'listo')

        # Cambiar a entregado
        pedido.estado = 'entregado'
        pedido.save()
        self.assertEqual(pedido.estado, 'entregado')


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
        """Test: Crear pedido desde API del cliente"""
        url = reverse('crear_pedido_cliente')  # Asegúrate de que esta URL exista
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

        # Nota: Esta API permite acceso sin autenticación (AllowAny)
        response = self.client.post(
            url,
            data=data,
            content_type='application/json'
        )

        # Verificar respuesta exitosa
        self.assertEqual(response.status_code, 201)
        response_data = response.json()
        self.assertTrue(response_data.get('success'))
        self.assertEqual(response_data.get('mesa'), self.mesa.numero)

        # Verificar que se creó el pedido
        pedido = Pedido.objects.filter(mesa=self.mesa).first()
        self.assertIsNotNone(pedido)
        self.assertEqual(pedido.total, Decimal('80.00'))

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
        pedido.estado = 'listo'
        pedido.save()
        self.assertEqual(pedido.estado, 'listo')

        # 5. Entregar
        pedido.estado = 'entregado'
        pedido.save()
        self.assertEqual(pedido.estado, 'entregado')

        # Verificar que el pedido tiene todos los datos correctos
        self.assertEqual(pedido.detalles.count(), 1)
        self.assertEqual(pedido.mesa.numero, 5)
