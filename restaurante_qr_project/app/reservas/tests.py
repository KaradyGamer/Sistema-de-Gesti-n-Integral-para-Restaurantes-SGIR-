from django.test import TestCase
from django.utils import timezone
from datetime import date, time, timedelta

from app.mesas.models import Mesa
from .models import Reserva
from .forms import ReservaForm


class ReservaModelTestCase(TestCase):
    """Tests para el modelo Reserva"""

    def setUp(self):
        """Configurar datos de prueba"""
        self.mesa = Mesa.objects.create(numero=5, capacidad=6)

    def test_crear_reserva(self):
        """Test: Crear una reserva básica"""
        fecha_reserva = date.today() + timedelta(days=1)
        reserva = Reserva.objects.create(
            numero_carnet='12345678',
            nombre_completo='Juan Pérez',
            telefono='70123456',
            email='juan@example.com',
            fecha_reserva=fecha_reserva,
            hora_reserva=time(19, 0),
            numero_personas=4,
            estado='pendiente'
        )

        self.assertEqual(reserva.nombre_completo, 'Juan Pérez')
        self.assertEqual(reserva.estado, 'pendiente')
        self.assertEqual(reserva.numero_personas, 4)

    def test_asignar_mesa_reserva(self):
        """Test: Asignar mesa a una reserva"""
        fecha_reserva = date.today() + timedelta(days=1)
        reserva = Reserva.objects.create(
            numero_carnet='87654321',
            nombre_completo='María García',
            telefono='71234567',
            fecha_reserva=fecha_reserva,
            hora_reserva=time(20, 0),
            numero_personas=6,
            estado='confirmada'
        )

        # Asignar mesa
        reserva.mesa = self.mesa
        reserva.save()

        self.assertEqual(reserva.mesa.numero, 5)
        self.assertEqual(reserva.mesa.capacidad, 6)

    def test_estados_reserva(self):
        """Test: Cambiar estados de reserva"""
        fecha_reserva = date.today() + timedelta(days=2)
        reserva = Reserva.objects.create(
            numero_carnet='11111111',
            nombre_completo='Pedro López',
            telefono='72345678',
            fecha_reserva=fecha_reserva,
            hora_reserva=time(18, 30),
            numero_personas=2,
            estado='pendiente'
        )

        # Confirmar reserva
        reserva.estado = 'confirmada'
        reserva.save()
        self.assertEqual(reserva.estado, 'confirmada')

        # Marcar como en uso
        reserva.estado = 'en_uso'
        reserva.save()
        self.assertEqual(reserva.estado, 'en_uso')

        # Completar
        reserva.estado = 'completada'
        reserva.save()
        self.assertEqual(reserva.estado, 'completada')

    def test_cancelar_reserva(self):
        """Test: Cancelar una reserva"""
        fecha_reserva = date.today() + timedelta(days=3)
        reserva = Reserva.objects.create(
            numero_carnet='22222222',
            nombre_completo='Ana Martínez',
            telefono='73456789',
            fecha_reserva=fecha_reserva,
            hora_reserva=time(21, 0),
            numero_personas=8,
            estado='confirmada'
        )

        # Cancelar
        reserva.estado = 'cancelada'
        reserva.save()

        self.assertEqual(reserva.estado, 'cancelada')


class ReservaFormTestCase(TestCase):
    """Tests para el formulario de reservas"""

    def test_form_valido(self):
        """Test: Formulario válido con datos correctos"""
        fecha_reserva = date.today() + timedelta(days=1)
        form_data = {
            'numero_carnet': '12345678',
            'nombre_completo': 'Carlos Rodríguez',
            'telefono': '74567890',
            'email': 'carlos@example.com',
            'fecha_reserva': fecha_reserva,
            'hora_reserva': time(19, 30),
            'numero_personas': 4,
            'observaciones': 'Mesa cerca de la ventana'
        }

        form = ReservaForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_fecha_pasada_invalida(self):
        """Test: No se puede reservar para fechas pasadas"""
        fecha_pasada = date.today() - timedelta(days=1)
        form_data = {
            'numero_carnet': '12345678',
            'nombre_completo': 'Carlos Rodríguez',
            'telefono': '74567890',
            'fecha_reserva': fecha_pasada,
            'hora_reserva': time(19, 30),
            'numero_personas': 4
        }

        form = ReservaForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('fecha_reserva', form.errors)

    def test_hora_fuera_horario_invalida(self):
        """Test: Hora fuera del horario de atención"""
        fecha_reserva = date.today() + timedelta(days=1)
        form_data = {
            'numero_carnet': '12345678',
            'nombre_completo': 'Carlos Rodríguez',
            'telefono': '74567890',
            'fecha_reserva': fecha_reserva,
            'hora_reserva': time(23, 0),  # Fuera del horario 11:00-22:00
            'numero_personas': 4
        }

        form = ReservaForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('hora_reserva', form.errors)

    def test_telefono_invalido(self):
        """Test: Validación de teléfono boliviano"""
        fecha_reserva = date.today() + timedelta(days=1)
        form_data = {
            'numero_carnet': '12345678',
            'nombre_completo': 'Carlos Rodríguez',
            'telefono': '123',  # Muy corto
            'fecha_reserva': fecha_reserva,
            'hora_reserva': time(19, 30),
            'numero_personas': 4
        }

        form = ReservaForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('telefono', form.errors)

    def test_numero_personas_invalido(self):
        """Test: Número de personas debe estar en rango válido"""
        fecha_reserva = date.today() + timedelta(days=1)
        form_data = {
            'numero_carnet': '12345678',
            'nombre_completo': 'Carlos Rodríguez',
            'telefono': '74567890',
            'fecha_reserva': fecha_reserva,
            'hora_reserva': time(19, 30),
            'numero_personas': 25  # Más de 20
        }

        form = ReservaForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('numero_personas', form.errors)

    def test_carnet_invalido_corto(self):
        """Test: Carnet debe tener al menos 6 dígitos"""
        fecha_reserva = date.today() + timedelta(days=1)
        form_data = {
            'numero_carnet': '123',  # Muy corto
            'nombre_completo': 'Carlos Rodríguez',
            'telefono': '74567890',
            'fecha_reserva': fecha_reserva,
            'hora_reserva': time(19, 30),
            'numero_personas': 4
        }

        form = ReservaForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('numero_carnet', form.errors)


class ReservaIntegracionTestCase(TestCase):
    """Tests de integración para reservas"""

    def setUp(self):
        """Configurar escenario completo"""
        # Crear mesas
        self.mesa_pequena = Mesa.objects.create(numero=1, capacidad=2)
        self.mesa_mediana = Mesa.objects.create(numero=2, capacidad=4)
        self.mesa_grande = Mesa.objects.create(numero=3, capacidad=8)

    def test_flujo_completo_reserva(self):
        """Test: Flujo completo de una reserva"""
        fecha_reserva = date.today() + timedelta(days=1)

        # 1. Crear reserva
        reserva = Reserva.objects.create(
            numero_carnet='99999999',
            nombre_completo='Luis Fernández',
            telefono='75678901',
            email='luis@example.com',
            fecha_reserva=fecha_reserva,
            hora_reserva=time(20, 0),
            numero_personas=4,
            estado='pendiente'
        )
        self.assertEqual(reserva.estado, 'pendiente')

        # 2. Confirmar reserva y asignar mesa
        reserva.estado = 'confirmada'
        reserva.mesa = self.mesa_mediana
        reserva.save()
        self.assertEqual(reserva.estado, 'confirmada')
        self.assertIsNotNone(reserva.mesa)

        # 3. Cliente llega - marcar en uso
        reserva.estado = 'en_uso'
        reserva.save()
        self.assertEqual(reserva.estado, 'en_uso')

        # 4. Cliente termina - completar
        reserva.estado = 'completada'
        reserva.save()
        self.assertEqual(reserva.estado, 'completada')

    def test_asignar_mesa_segun_capacidad(self):
        """Test: Asignar mesa adecuada según número de personas"""
        fecha_reserva = date.today() + timedelta(days=1)

        # Reserva para 2 personas
        reserva_2 = Reserva.objects.create(
            numero_carnet='11111111',
            nombre_completo='Pareja',
            telefono='70111111',
            fecha_reserva=fecha_reserva,
            hora_reserva=time(19, 0),
            numero_personas=2,
            mesa=self.mesa_pequena
        )
        self.assertEqual(reserva_2.mesa.capacidad, 2)

        # Reserva para 8 personas
        reserva_8 = Reserva.objects.create(
            numero_carnet='88888888',
            nombre_completo='Grupo grande',
            telefono='70888888',
            fecha_reserva=fecha_reserva,
            hora_reserva=time(20, 0),
            numero_personas=8,
            mesa=self.mesa_grande
        )
        self.assertEqual(reserva_8.mesa.capacidad, 8)

    def test_multiples_reservas_mismo_dia(self):
        """Test: Múltiples reservas para el mismo día"""
        fecha_reserva = date.today() + timedelta(days=1)

        reserva_1 = Reserva.objects.create(
            numero_carnet='11111111',
            nombre_completo='Reserva 1',
            telefono='70111111',
            fecha_reserva=fecha_reserva,
            hora_reserva=time(18, 0),
            numero_personas=2
        )

        reserva_2 = Reserva.objects.create(
            numero_carnet='22222222',
            nombre_completo='Reserva 2',
            telefono='70222222',
            fecha_reserva=fecha_reserva,
            hora_reserva=time(19, 0),
            numero_personas=4
        )

        reserva_3 = Reserva.objects.create(
            numero_carnet='33333333',
            nombre_completo='Reserva 3',
            telefono='70333333',
            fecha_reserva=fecha_reserva,
            hora_reserva=time(20, 0),
            numero_personas=6
        )

        # Verificar que todas se crearon para el mismo día
        reservas_del_dia = Reserva.objects.filter(fecha_reserva=fecha_reserva)
        self.assertEqual(reservas_del_dia.count(), 3)
