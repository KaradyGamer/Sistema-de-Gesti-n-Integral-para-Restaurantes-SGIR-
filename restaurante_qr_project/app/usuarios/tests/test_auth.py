"""
Tests de autenticación - Login QR, PIN y Password
"""
from django.test import TestCase, Client
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta
from app.usuarios.models import Usuario, QRToken


class QRLoginTestCase(TestCase):
    """Tests para login por QR"""

    def setUp(self):
        self.client = Client()
        self.mesero = Usuario.objects.create_user(
            username='mesero_test',
            password='test123',
            rol='mesero',
            activo=True
        )
        cache.clear()  # Limpiar cache para rate limiting

    def test_qr_login_exitoso(self):
        """✅ Login exitoso con token QR válido"""
        token = QRToken.generar_token(self.mesero, '127.0.0.1', duracion_horas=24)

        response = self.client.get(f'/qr-login/{token.token}/')

        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertTrue('/mesero/' in response.url)

        # Verificar que el token fue marcado como usado
        token.refresh_from_db()
        self.assertTrue(token.usado)
        self.assertFalse(token.activo)

    def test_qr_login_token_expirado(self):
        """❌ Login rechazado con token expirado"""
        token = QRToken.objects.create(
            usuario=self.mesero,
            activo=True,
            fecha_expiracion=timezone.now() - timedelta(hours=1)  # Expirado
        )

        response = self.client.get(f'/qr-login/{token.token}/')

        self.assertEqual(response.status_code, 302)  # Redirect a login
        self.assertTrue('/login/' in response.url)

        # Verificar que el token fue invalidado
        token.refresh_from_db()
        self.assertFalse(token.activo)

    def test_qr_login_token_invalido(self):
        """❌ Login rechazado con token inexistente"""
        import uuid
        token_falso = uuid.uuid4()

        response = self.client.get(f'/qr-login/{token_falso}/')

        self.assertEqual(response.status_code, 302)
        self.assertTrue('/login/' in response.url)

    def test_qr_token_un_solo_uso(self):
        """🔒 Token solo puede usarse una vez"""
        token = QRToken.generar_token(self.mesero, '127.0.0.1')

        # Primer uso
        self.client.get(f'/qr-login/{token.token}/')

        # Segundo uso debe fallar
        self.client.logout()
        response = self.client.get(f'/qr-login/{token.token}/')

        self.assertEqual(response.status_code, 302)
        self.assertTrue('/login/' in response.url)


class PINLoginTestCase(TestCase):
    """Tests para login por PIN"""

    def setUp(self):
        self.client = Client()
        self.cajero = Usuario.objects.create_user(
            username='cajero_test',
            password='test123',
            rol='cajero',
            pin='1234',
            activo=True
        )
        cache.clear()

    def test_pin_login_exitoso(self):
        """✅ Login exitoso con PIN válido"""
        response = self.client.post(
            '/usuarios/login-pin/',
            data='{"pin": "1234"}',
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['rol'], 'cajero')

    def test_pin_login_invalido(self):
        """❌ Login rechazado con PIN inválido"""
        response = self.client.post(
            '/usuarios/login-pin/',
            data='{"pin": "9999"}',
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertFalse(data['success'])

    def test_pin_rate_limiting(self):
        """🔒 Rate limiting tras 5 intentos fallidos"""
        # 5 intentos con PIN inválido
        for i in range(5):
            self.client.post(
                '/usuarios/login-pin/',
                data='{"pin": "9999"}',
                content_type='application/json'
            )

        # El 6to intento debe ser bloqueado
        response = self.client.post(
            '/usuarios/login-pin/',
            data='{"pin": "1234"}',  # Incluso con PIN correcto
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 429)  # Too Many Requests


class PasswordLoginTestCase(TestCase):
    """Tests para login por usuario/contraseña"""

    def setUp(self):
        self.client = Client()
        self.admin = Usuario.objects.create_user(
            username='admin_test',
            password='admin123',
            rol='admin',
            activo=True
        )
        cache.clear()

    def test_password_login_exitoso(self):
        """✅ Login exitoso con credenciales válidas"""
        response = self.client.post(
            '/usuarios/session-login/',
            data={
                'username': 'admin_test',
                'password': 'admin123',
                'rol': 'administrador'
            }
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])

    def test_password_login_credenciales_invalidas(self):
        """❌ Login rechazado con contraseña incorrecta"""
        response = self.client.post(
            '/usuarios/session-login/',
            data={
                'username': 'admin_test',
                'password': 'wrongpassword',
                'rol': 'administrador'
            }
        )

        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertFalse(data['success'])

    def test_password_login_usuario_inactivo(self):
        """❌ Login rechazado si usuario está inactivo"""
        self.admin.activo = False
        self.admin.save()

        response = self.client.post(
            '/usuarios/session-login/',
            data={
                'username': 'admin_test',
                'password': 'admin123',
                'rol': 'administrador'
            }
        )

        self.assertEqual(response.status_code, 400)
