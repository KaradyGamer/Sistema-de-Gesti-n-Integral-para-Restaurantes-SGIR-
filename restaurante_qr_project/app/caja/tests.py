from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from datetime import date

from app.usuarios.models import Usuario
from app.mesas.models import Mesa
from app.productos.models import Producto, Categoria
from app.pedidos.models import Pedido, DetallePedido
from .models import Transaccion, CierreCaja, DetallePago
from .utils import (
    generar_numero_factura,
    calcular_cambio,
    validar_stock_pedido,
    calcular_total_con_descuento_propina
)


class TransaccionModelTestCase(TestCase):
    """Tests para el modelo Transacción"""

    def setUp(self):
        """Configurar datos de prueba"""
        self.cajero = Usuario.objects.create_user(
            username='cajero1',
            password='pass123',
            rol='cajero'
        )
        self.mesa = Mesa.objects.create(numero=1, capacidad=4)
        self.pedido = Pedido.objects.create(
            mesa=self.mesa,
            fecha=timezone.now(),
            forma_pago='efectivo',
            estado='listo',
            total=Decimal('50.00')
        )

    def test_crear_transaccion_efectivo(self):
        """Test: Crear transacción con pago en efectivo"""
        transaccion = Transaccion.objects.create(
            pedido=self.pedido,
            cajero=self.cajero,
            monto_total=Decimal('50.00'),
            metodo_pago='efectivo',
            estado='procesado',
            numero_factura='FAC-001'
        )

        self.assertEqual(transaccion.monto_total, Decimal('50.00'))
        self.assertEqual(transaccion.metodo_pago, 'efectivo')
        self.assertEqual(transaccion.estado, 'procesado')
        self.assertIsNotNone(transaccion.numero_factura)

    def test_crear_transaccion_tarjeta(self):
        """Test: Crear transacción con pago en tarjeta"""
        transaccion = Transaccion.objects.create(
            pedido=self.pedido,
            cajero=self.cajero,
            monto_total=Decimal('50.00'),
            metodo_pago='tarjeta',
            estado='procesado',
            numero_factura='FAC-002',
            referencia='REF123456'
        )

        self.assertEqual(transaccion.metodo_pago, 'tarjeta')
        self.assertIsNotNone(transaccion.referencia)

    def test_transaccion_mixta(self):
        """Test: Transacción con pago mixto (efectivo + tarjeta)"""
        transaccion = Transaccion.objects.create(
            pedido=self.pedido,
            cajero=self.cajero,
            monto_total=Decimal('100.00'),
            metodo_pago='mixto',
            estado='procesado',
            numero_factura='FAC-003'
        )

        # Crear detalles de pago
        DetallePago.objects.create(
            transaccion=transaccion,
            metodo_pago='efectivo',
            monto=Decimal('50.00')
        )
        DetallePago.objects.create(
            transaccion=transaccion,
            metodo_pago='tarjeta',
            monto=Decimal('50.00'),
            referencia='REF789'
        )

        self.assertEqual(transaccion.detalles_pago.count(), 2)
        total_detalles = sum(d.monto for d in transaccion.detalles_pago.all())
        self.assertEqual(total_detalles, Decimal('100.00'))


class CierreCajaModelTestCase(TestCase):
    """Tests para el modelo CierreCaja"""

    def setUp(self):
        """Configurar datos de prueba"""
        self.cajero = Usuario.objects.create_user(
            username='cajero1',
            password='pass123',
            rol='cajero'
        )

    def test_abrir_caja(self):
        """Test: Abrir un turno de caja"""
        cierre = CierreCaja.objects.create(
            cajero=self.cajero,
            fecha=date.today(),
            turno='mañana',
            estado='abierto',
            efectivo_inicial=Decimal('100.00')
        )

        self.assertEqual(cierre.estado, 'abierto')
        self.assertEqual(cierre.efectivo_inicial, Decimal('100.00'))
        self.assertIsNotNone(cierre.hora_apertura)
        self.assertIsNone(cierre.hora_cierre)

    def test_cerrar_caja(self):
        """Test: Cerrar un turno de caja"""
        cierre = CierreCaja.objects.create(
            cajero=self.cajero,
            fecha=date.today(),
            turno='tarde',
            estado='abierto',
            efectivo_inicial=Decimal('100.00')
        )

        # Cerrar caja
        cierre.cerrar_caja(
            efectivo_real=Decimal('450.00'),
            observaciones='Cierre normal'
        )

        self.assertEqual(cierre.estado, 'cerrado')
        self.assertEqual(cierre.efectivo_real, Decimal('450.00'))
        self.assertIsNotNone(cierre.hora_cierre)

    def test_calcular_diferencia_caja(self):
        """Test: Calcular diferencia entre efectivo esperado y real"""
        cierre = CierreCaja.objects.create(
            cajero=self.cajero,
            fecha=date.today(),
            turno='completo',
            estado='abierto',
            efectivo_inicial=Decimal('100.00'),
            efectivo_esperado=Decimal('500.00')
        )

        # Cerrar con diferencia
        cierre.cerrar_caja(efectivo_real=Decimal('495.00'))

        diferencia_esperada = Decimal('495.00') - Decimal('500.00')
        self.assertEqual(cierre.diferencia, diferencia_esperada)


class UtilsTestCase(TestCase):
    """Tests para funciones utilitarias de caja"""

    def test_generar_numero_factura(self):
        """Test: Generar número de factura único"""
        factura1 = generar_numero_factura()
        factura2 = generar_numero_factura()

        self.assertIsNotNone(factura1)
        self.assertIsNotNone(factura2)
        self.assertNotEqual(factura1, factura2)  # Deben ser diferentes
        self.assertTrue(factura1.startswith('FAC-'))

    def test_calcular_cambio(self):
        """Test: Calcular cambio correctamente"""
        total = Decimal('47.50')
        monto_recibido = Decimal('50.00')
        cambio = calcular_cambio(total, monto_recibido)

        self.assertEqual(cambio, Decimal('2.50'))

    def test_calcular_cambio_exacto(self):
        """Test: Sin cambio cuando el monto es exacto"""
        total = Decimal('100.00')
        monto_recibido = Decimal('100.00')
        cambio = calcular_cambio(total, monto_recibido)

        self.assertEqual(cambio, Decimal('0.00'))

    def test_calcular_total_con_descuento(self):
        """Test: Calcular total con descuento"""
        mesa = Mesa.objects.create(numero=1, capacidad=4)
        pedido = Pedido.objects.create(
            mesa=mesa,
            fecha=timezone.now(),
            forma_pago='efectivo',
            estado='listo',
            total=Decimal('100.00'),
            descuento=Decimal('10.00')  # 10% de descuento
        )

        total_final = calcular_total_con_descuento_propina(pedido)
        self.assertEqual(total_final, Decimal('90.00'))

    def test_calcular_total_con_propina(self):
        """Test: Calcular total con propina"""
        mesa = Mesa.objects.create(numero=1, capacidad=4)
        pedido = Pedido.objects.create(
            mesa=mesa,
            fecha=timezone.now(),
            forma_pago='efectivo',
            estado='listo',
            total=Decimal('100.00'),
            propina=Decimal('10.00')  # 10 Bs de propina
        )

        total_final = calcular_total_con_descuento_propina(pedido)
        self.assertEqual(total_final, Decimal('110.00'))

    def test_validar_stock_producto_disponible(self):
        """Test: Validar stock de producto con inventario suficiente"""
        categoria = Categoria.objects.create(nombre='Bebidas')
        producto = Producto.objects.create(
            nombre='Coca Cola',
            precio=Decimal('5.00'),
            categoria=categoria,
            disponible=True,
            requiere_inventario=True,
            stock_actual=50,
            stock_minimo=10
        )

        mesa = Mesa.objects.create(numero=1, capacidad=4)
        pedido = Pedido.objects.create(
            mesa=mesa,
            fecha=timezone.now(),
            forma_pago='efectivo',
            estado='listo',
            total=Decimal('10.00')
        )
        DetallePedido.objects.create(
            pedido=pedido,
            producto=producto,
            cantidad=2,
            subtotal=Decimal('10.00')
        )

        es_valido, productos_sin_stock = validar_stock_pedido(pedido)
        self.assertTrue(es_valido)
        self.assertEqual(len(productos_sin_stock), 0)


class IntegracionCajaTestCase(TestCase):
    """Tests de integración para flujo completo de caja"""

    def setUp(self):
        """Configurar escenario completo"""
        self.cajero = Usuario.objects.create_user(
            username='cajero1',
            password='pass123',
            rol='cajero'
        )
        self.mesa = Mesa.objects.create(numero=1, capacidad=4)
        self.categoria = Categoria.objects.create(nombre='Comida')
        self.producto = Producto.objects.create(
            nombre='Hamburguesa',
            precio=Decimal('30.00'),
            categoria=self.categoria,
            disponible=True
        )

    def test_flujo_completo_pago(self):
        """Test: Flujo completo desde pedido hasta pago"""
        # 1. Abrir caja
        cierre = CierreCaja.objects.create(
            cajero=self.cajero,
            fecha=date.today(),
            turno='completo',
            estado='abierto',
            efectivo_inicial=Decimal('200.00')
        )
        self.assertEqual(cierre.estado, 'abierto')

        # 2. Crear pedido
        pedido = Pedido.objects.create(
            mesa=self.mesa,
            fecha=timezone.now(),
            forma_pago='efectivo',
            estado='listo'
        )
        DetallePedido.objects.create(
            pedido=pedido,
            producto=self.producto,
            cantidad=2,
            subtotal=self.producto.precio * 2
        )
        pedido.total = self.producto.precio * 2
        pedido.save()

        # 3. Procesar pago
        transaccion = Transaccion.objects.create(
            pedido=pedido,
            cajero=self.cajero,
            monto_total=pedido.total,
            metodo_pago='efectivo',
            estado='procesado',
            numero_factura=generar_numero_factura()
        )

        # 4. Actualizar pedido
        pedido.estado_pago = 'pagado'
        pedido.fecha_pago = timezone.now()
        pedido.cajero_responsable = self.cajero
        pedido.save()

        # Verificaciones
        self.assertEqual(pedido.estado_pago, 'pagado')
        self.assertEqual(transaccion.estado, 'procesado')
        self.assertEqual(transaccion.monto_total, Decimal('60.00'))

        # 5. Cerrar caja
        efectivo_total = cierre.efectivo_inicial + pedido.total
        cierre.cerrar_caja(efectivo_real=efectivo_total)

        self.assertEqual(cierre.estado, 'cerrado')
        self.assertIsNotNone(cierre.hora_cierre)
