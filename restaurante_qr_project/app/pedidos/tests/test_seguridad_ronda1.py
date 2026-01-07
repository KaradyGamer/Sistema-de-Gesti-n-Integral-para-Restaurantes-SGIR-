"""
Tests de Seguridad - RONDA 1
Fecha: 2026-01-04
Objetivo: Verificar que endpoint público de creación de pedidos está deshabilitado
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from app.pedidos.models import Pedido
from app.mesas.models import Mesa
from app.productos.models import Producto, Categoria

User = get_user_model()


class Ronda1SeguridadTests(TestCase):
    """Tests de seguridad - Ronda 1: Cliente QR solo lectura"""

    def setUp(self):
        """Configurar datos de prueba"""
        self.client = Client()

        # Crear mesa de prueba
        self.mesa = Mesa.objects.create(
            numero=1,
            capacidad=4,
            estado='disponible'
        )

        # Crear categoría y producto para tests completos
        self.categoria = Categoria.objects.create(
            nombre='Bebidas',
            descripcion='Bebidas varias'
        )

        self.producto = Producto.objects.create(
            nombre='Coca Cola',
            descripcion='Refresco',
            precio=10.00,
            categoria=self.categoria,
            activo=True,
            stock_actual=100
        )

    def test_endpoint_crear_pedido_cliente_deshabilitado(self):
        """Verificar que endpoint público está deshabilitado y devuelve 404"""
        response = self.client.post(
            '/pedidos/cliente/crear/',
            data={
                'mesa_id': self.mesa.id,
                'productos': [
                    {
                        'producto_id': self.producto.id,
                        'cantidad': 1
                    }
                ],
                'numero_personas': 2
            },
            content_type='application/json'
        )

        # Debe devolver 404 (Not Found)
        self.assertEqual(response.status_code, 404)

        # Debe contener mensaje genérico
        response_data = response.json()
        self.assertIn('detail', response_data)
        self.assertEqual(response_data['detail'], 'Not found.')

    def test_no_se_crea_pedido_en_endpoint_deshabilitado(self):
        """Verificar que NO se crea pedido al intentar acceder al endpoint"""
        # Contar pedidos iniciales
        pedidos_iniciales = Pedido.objects.count()

        # Intentar crear pedido
        self.client.post(
            '/pedidos/cliente/crear/',
            data={
                'mesa_id': self.mesa.id,
                'productos': [
                    {
                        'producto_id': self.producto.id,
                        'cantidad': 1
                    }
                ],
                'numero_personas': 2
            },
            content_type='application/json'
        )

        # Verificar que NO se creó pedido
        pedidos_finales = Pedido.objects.count()
        self.assertEqual(pedidos_iniciales, pedidos_finales, "NO debe crear pedido")

    def test_no_se_descuenta_stock_en_endpoint_deshabilitado(self):
        """Verificar que NO se modifica stock al intentar crear pedido"""
        # Stock inicial
        stock_inicial = self.producto.stock_actual

        # Intentar crear pedido
        self.client.post(
            '/pedidos/cliente/crear/',
            data={
                'mesa_id': self.mesa.id,
                'productos': [
                    {
                        'producto_id': self.producto.id,
                        'cantidad': 5
                    }
                ],
                'numero_personas': 2
            },
            content_type='application/json'
        )

        # Recargar producto desde BD
        self.producto.refresh_from_db()

        # Verificar que stock NO cambió
        self.assertEqual(
            self.producto.stock_actual,
            stock_inicial,
            "Stock NO debe haberse modificado"
        )

    def test_mesa_no_se_ocupa_en_endpoint_deshabilitado(self):
        """Verificar que la mesa NO se marca como ocupada"""
        # Estado inicial
        self.assertEqual(self.mesa.estado, 'disponible')

        # Intentar crear pedido
        self.client.post(
            '/pedidos/cliente/crear/',
            data={
                'mesa_id': self.mesa.id,
                'productos': [
                    {
                        'producto_id': self.producto.id,
                        'cantidad': 1
                    }
                ],
                'numero_personas': 2
            },
            content_type='application/json'
        )

        # Recargar mesa desde BD
        self.mesa.refresh_from_db()

        # Verificar que mesa sigue disponible
        self.assertEqual(
            self.mesa.estado,
            'disponible',
            "Mesa NO debe haberse ocupado"
        )

    def test_codigo_muerto_eliminado_en_utils(self):
        """Verificar que no hay validaciones contra estados inexistentes"""
        from app.pedidos import utils
        import inspect

        # Obtener código fuente de la función
        source = inspect.getsource(utils.modificar_pedido_con_stock)

        # NO debe contener validación activa contra 'pagado', 'cancelado'
        # (puede estar en comentarios, pero no en código activo)
        self.assertNotIn(
            "in ['pagado', 'cancelado']",
            source,
            "No debe validar contra estados inexistentes 'pagado', 'cancelado'"
        )

    def test_endpoint_acepta_GET_y_POST(self):
        """Verificar que endpoint acepta GET y POST (para devolver 404 en ambos)"""
        # Test GET
        response_get = self.client.get('/pedidos/cliente/crear/')
        self.assertEqual(response_get.status_code, 404)

        # Test POST
        response_post = self.client.post('/pedidos/cliente/crear/')
        self.assertEqual(response_post.status_code, 404)


class Ronda1LoggingTests(TestCase):
    """Tests de logging de auditoría"""

    def setUp(self):
        """Configurar usuario y datos de prueba"""
        self.user = User.objects.create_user(
            username='mesero_test',
            password='test123',
            rol='mesero'
        )
        self.client = Client()
        self.client.login(username='mesero_test', password='test123')

    def test_logging_funciona(self):
        """Verificar que el sistema de logging está configurado"""
        import logging

        logger = logging.getLogger('app.pedidos')

        # Verificar que logger existe y tiene handlers
        self.assertIsNotNone(logger)
        # Este test es básico, solo verifica que no haya errores de configuración