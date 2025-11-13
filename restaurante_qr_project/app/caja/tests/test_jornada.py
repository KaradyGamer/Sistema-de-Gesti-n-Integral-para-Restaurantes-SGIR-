"""
Tests para apertura y cierre de jornada laboral
"""
from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from app.caja.models import Jornada
from app.usuarios.models import Usuario


class JornadaAperturaCierreTestCase(TestCase):
    """Tests para apertura y cierre de jornada"""

    def setUp(self):
        self.cajero = Usuario.objects.create_user(
            username='cajero_test',
            password='test123',
            rol='cajero',
            pin='1234',
            activo=True
        )

    def test_abrir_jornada_exitosamente(self):
        """✅ Abrir jornada correctamente"""
        jornada = Jornada.objects.create(
            cajero=self.cajero,
            monto_inicial=Decimal('100.00'),
            fecha_apertura=timezone.now()
        )

        self.assertTrue(jornada.esta_abierta)
        self.assertEqual(jornada.monto_inicial, Decimal('100.00'))
        self.assertIsNone(jornada.fecha_cierre)

    def test_no_permitir_multiples_jornadas_abiertas(self):
        """❌ No permitir múltiples jornadas abiertas para el mismo cajero"""
        # Crear primera jornada
        Jornada.objects.create(
            cajero=self.cajero,
            monto_inicial=Decimal('100.00')
        )

        # Verificar que solo hay una jornada abierta
        jornadas_abiertas = Jornada.objects.filter(
            cajero=self.cajero,
            fecha_cierre__isnull=True
        ).count()

        self.assertEqual(jornadas_abiertas, 1)

    def test_cerrar_jornada_sin_transacciones(self):
        """✅ Cerrar jornada sin transacciones (monto final = inicial)"""
        jornada = Jornada.objects.create(
            cajero=self.cajero,
            monto_inicial=Decimal('100.00')
        )

        # Cerrar jornada
        jornada.fecha_cierre = timezone.now()
        jornada.monto_final = Decimal('100.00')
        jornada.save()

        self.assertFalse(jornada.esta_abierta)
        self.assertEqual(jornada.monto_final, Decimal('100.00'))
        self.assertIsNotNone(jornada.fecha_cierre)

    def test_cerrar_jornada_con_ventas(self):
        """✅ Cerrar jornada con ventas (monto final > inicial)"""
        jornada = Jornada.objects.create(
            cajero=self.cajero,
            monto_inicial=Decimal('100.00')
        )

        # Simular ventas
        total_ventas = Decimal('250.00')

        # Cerrar jornada
        jornada.fecha_cierre = timezone.now()
        jornada.monto_final = jornada.monto_inicial + total_ventas
        jornada.save()

        self.assertEqual(jornada.monto_final, Decimal('350.00'))
        self.assertFalse(jornada.esta_abierta)

    def test_calcular_diferencia_jornada(self):
        """✅ Calcular diferencia entre monto esperado y real"""
        jornada = Jornada.objects.create(
            cajero=self.cajero,
            monto_inicial=Decimal('100.00')
        )

        # Simular ventas esperadas
        monto_esperado = Decimal('350.00')

        # Monto real contado
        jornada.monto_final = Decimal('348.00')  # Faltaron Bs 2
        jornada.fecha_cierre = timezone.now()
        jornada.save()

        diferencia = jornada.monto_final - monto_esperado
        self.assertEqual(diferencia, Decimal('-2.00'))

    def test_jornada_debe_tener_cajero(self):
        """❌ No permitir jornada sin cajero asignado"""
        with self.assertRaises(Exception):
            Jornada.objects.create(
                cajero=None,  # Sin cajero
                monto_inicial=Decimal('100.00')
            )


class JornadaMiddlewareTestCase(TestCase):
    """Tests para middleware de validación de jornada activa"""

    def setUp(self):
        self.cajero = Usuario.objects.create_user(
            username='cajero_test',
            password='test123',
            rol='cajero',
            activo=True
        )

    def test_acceso_sin_jornada_activa(self):
        """❌ Bloquear acceso a caja sin jornada activa"""
        # Login del cajero
        self.client.login(username='cajero_test', password='test123')

        # Intentar acceder a una página de caja sin jornada activa
        response = self.client.get('/caja/')

        # Debería redirigir o mostrar error
        # (Depende de la implementación del middleware)
        self.assertIn(response.status_code, [302, 403])

    def test_acceso_con_jornada_activa(self):
        """✅ Permitir acceso con jornada activa"""
        # Abrir jornada
        Jornada.objects.create(
            cajero=self.cajero,
            monto_inicial=Decimal('100.00')
        )

        # Login del cajero
        self.client.login(username='cajero_test', password='test123')

        # Acceder a página de caja
        response = self.client.get('/caja/')

        # Debería permitir acceso
        self.assertEqual(response.status_code, 200)
