"""
Tests para el sistema de login del personal (staff_login)
SGIR v38.8

Verifica:
- Ruteo automático según privilegios (superuser → /admin/, staff → /adminux/)
- Manejo de credenciales inválidas
- Usuarios inactivos
- Parámetro ?next= para redirecciones
- Template de login se renderiza correctamente
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model

User = get_user_model()


class StaffLoginTests(TestCase):
    """Tests para el login del personal"""

    def setUp(self):
        self.client = Client()

        # Crear usuarios de prueba
        self.superuser = User.objects.create_user(
            username="admin_super",
            password="admin123",
            is_superuser=True,
            is_staff=True,
            is_active=True,
            rol="Administrador"
        )

        self.staff_user = User.objects.create_user(
            username="staff_user",
            password="staff123",
            is_superuser=False,
            is_staff=True,
            is_active=True,
            rol="Cajero"
        )

        self.normal_user = User.objects.create_user(
            username="normal_user",
            password="normal123",
            is_superuser=False,
            is_staff=False,
            is_active=True,
            rol="Mesero"
        )

        self.inactive_user = User.objects.create_user(
            username="inactive_user",
            password="inactive123",
            is_superuser=False,
            is_staff=True,
            is_active=False,  # Usuario inactivo
            rol="Cocinero"
        )

    def test_login_page_renders(self):
        """La página de login debe renderizarse correctamente"""
        response = self.client.get("/staff/login/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Acceso del Personal")
        self.assertContains(response, "Usuario")
        self.assertContains(response, "Contraseña")

    def test_superuser_redirects_to_admin(self):
        """Superuser debe ser redirigido a /admin/"""
        response = self.client.post("/staff/login/", {
            "username": "admin_super",
            "password": "admin123"
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/admin/")

    def test_staff_user_redirects_to_adminux(self):
        """Usuario staff (no superuser) debe ser redirigido a /adminux/"""
        response = self.client.post("/staff/login/", {
            "username": "staff_user",
            "password": "staff123"
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/adminux/")

    def test_normal_user_redirects_to_home(self):
        """Usuario normal (no staff) debe ser redirigido a /"""
        response = self.client.post("/staff/login/", {
            "username": "normal_user",
            "password": "normal123"
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")

    def test_invalid_credentials(self):
        """Credenciales inválidas deben mostrar error"""
        response = self.client.post("/staff/login/", {
            "username": "invalid_user",
            "password": "wrong_password"
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Usuario o contraseña incorrectos")

    def test_inactive_user_cannot_login(self):
        """Usuarios inactivos no pueden iniciar sesión"""
        response = self.client.post("/staff/login/", {
            "username": "inactive_user",
            "password": "inactive123"
        })
        self.assertEqual(response.status_code, 200)
        # Django's authenticate() returns None for inactive users
        # So the error message is "Usuario o contraseña incorrectos"
        self.assertContains(response, "Usuario o contraseña incorrectos")

    def test_next_parameter_respected_for_adminux(self):
        """El parámetro ?next= debe respetarse si apunta a /adminux/"""
        response = self.client.post("/staff/login/?next=/adminux/usuarios/", {
            "username": "staff_user",
            "password": "staff123"
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/adminux/usuarios/")

    def test_next_parameter_ignored_if_not_adminux(self):
        """El parámetro ?next= debe ignorarse si no apunta a /adminux/"""
        response = self.client.post("/staff/login/?next=/some/other/path/", {
            "username": "staff_user",
            "password": "staff123"
        })
        # Debe redirigir a /adminux/ (por privilegios) ignorando el next
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/adminux/")

    def test_already_authenticated_superuser_redirects(self):
        """Superuser ya autenticado debe ser redirigido automáticamente"""
        self.client.login(username="admin_super", password="admin123")
        response = self.client.get("/staff/login/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/admin/")

    def test_already_authenticated_staff_redirects(self):
        """Staff ya autenticado debe ser redirigido automáticamente"""
        self.client.login(username="staff_user", password="staff123")
        response = self.client.get("/staff/login/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/adminux/")

    def test_csrf_protection(self):
        """La vista debe tener el decorator @csrf_protect"""
        # Django's test client automatically includes CSRF tokens
        # This test verifies the decorator is present, not that it blocks requests
        from app.adminux.views import staff_login
        import inspect

        # Check if the function has @csrf_protect decorator
        source = inspect.getsource(staff_login)
        self.assertIn("@csrf_protect", source)


class AdminUXAccessWithNewLoginTests(TestCase):
    """Tests para verificar que AdminUX usa el nuevo login"""

    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username="staff_test",
            password="test123",
            is_staff=True,
            is_active=True,
            rol="Cajero"
        )

    def test_adminux_without_login_redirects_to_staff_login(self):
        """Acceso a /adminux/ sin login debe redirigir a /staff/login/"""
        response = self.client.get("/adminux/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/staff/login/", response.url)

    def test_adminux_login_endpoint_also_works(self):
        """/adminux/login/ también debe funcionar (ruta alternativa)"""
        response = self.client.get("/adminux/login/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Acceso del Personal")
