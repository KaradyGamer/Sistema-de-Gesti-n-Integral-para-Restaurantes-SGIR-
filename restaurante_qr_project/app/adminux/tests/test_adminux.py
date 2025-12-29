"""
Tests para el Panel AdminUX
SGIR v38.8

Verifica:
- Autenticación requerida (staff-only)
- Redirección al login del admin nativo
- Carga correcta del dashboard
- Enlaces no provocan errores
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model

User = get_user_model()


class AdminUXAccessTests(TestCase):
    """Tests de acceso y autenticación al panel AdminUX"""

    def setUp(self):
        self.client = Client()

        # Usuario staff (puede acceder)
        self.staff_user = User.objects.create_user(
            username="adminux_test",
            password="pass12345",
            is_staff=True,
            is_active=True,
            rol="Administrador"
        )

        # Usuario normal (NO puede acceder)
        self.normal_user = User.objects.create_user(
            username="normal_test",
            password="pass12345",
            is_staff=False,
            is_active=True,
            rol="Mesero"
        )

    def test_requires_login(self):
        """Acceso sin login debe redirigir a /admin/login/"""
        response = self.client.get("/adminux/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_requires_staff(self):
        """Usuario normal (no staff) debe ser redirigido"""
        self.client.login(username="normal_test", password="pass12345")
        response = self.client.get("/adminux/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_staff_access_ok(self):
        """Usuario staff debe acceder correctamente"""
        self.client.login(username="adminux_test", password="pass12345")
        response = self.client.get("/adminux/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Panel Administrativo")

    def test_dashboard_has_kpis(self):
        """Dashboard debe mostrar las secciones de KPIs"""
        self.client.login(username="adminux_test", password="pass12345")
        response = self.client.get("/adminux/")

        # Verificar que contiene las secciones principales
        self.assertContains(response, "Mesas")
        self.assertContains(response, "Productos")
        self.assertContains(response, "Pedidos")
        self.assertContains(response, "Caja")
        self.assertContains(response, "Reservas")
        self.assertContains(response, "Usuarios")


class AdminUXHelperFunctionsTests(TestCase):
    """Tests de las funciones helper del módulo adminux"""

    def test_safe_get_model_existing(self):
        """safe_get_model debe retornar modelo existente"""
        from app.adminux.views import safe_get_model

        Mesa = safe_get_model("mesas", "Mesa")
        self.assertIsNotNone(Mesa)
        self.assertEqual(Mesa._meta.model_name, "mesa")

    def test_safe_get_model_nonexisting(self):
        """safe_get_model debe retornar None para modelo inexistente"""
        from app.adminux.views import safe_get_model

        FakeModel = safe_get_model("fake_app", "FakeModel")
        self.assertIsNone(FakeModel)

    def test_admin_url_for_registered_model(self):
        """admin_url_for debe generar URL para modelo registrado"""
        from app.adminux.views import admin_url_for, safe_get_model

        Mesa = safe_get_model("mesas", "Mesa")
        url = admin_url_for(Mesa)

        # Debe ser una URL válida, no '#'
        self.assertNotEqual(url, "#")
        self.assertIn("/admin/mesas/mesa/", url)

    def test_admin_url_for_none_model(self):
        """admin_url_for debe retornar '#' si modelo es None"""
        from app.adminux.views import admin_url_for

        url = admin_url_for(None)
        self.assertEqual(url, "#")

    def test_safe_count_with_valid_filter(self):
        """safe_count debe funcionar con filtros válidos"""
        from app.adminux.views import safe_count
        from app.usuarios.models import Usuario

        # Crear 3 usuarios activos
        for i in range(3):
            Usuario.objects.create_user(
                username=f"user{i}",
                password="pass",
                is_active=True,
                activo=True,
                rol="Mesero"
            )

        count = safe_count(Usuario.objects, is_active=True)
        self.assertGreaterEqual(count, 3)

    def test_safe_count_with_invalid_filter(self):
        """safe_count debe hacer fallback si filtro es inválido"""
        from app.adminux.views import safe_count
        from app.usuarios.models import Usuario

        # Intentar filtrar por campo inexistente
        count = safe_count(Usuario.objects, campo_que_no_existe=True)

        # Debe retornar count() general sin crashear
        self.assertIsInstance(count, int)
        self.assertGreaterEqual(count, 0)


class AdminUXDashboardRenderingTests(TestCase):
    """Tests de renderizado y contenido del dashboard"""

    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username="admin",
            password="admin123",
            is_staff=True,
            is_active=True,
            rol="Administrador"
        )
        self.client.login(username="admin", password="admin123")

    def test_links_do_not_crash(self):
        """Los enlaces del dashboard no deben provocar errores"""
        response = self.client.get("/adminux/")
        self.assertEqual(response.status_code, 200)

        # Verificar que hay enlaces href (aunque sean '#')
        content = response.content.decode("utf-8")
        self.assertIn("href", content)

        # No debe haber errores de template
        self.assertNotContains(response, "TemplateSyntaxError")
        self.assertNotContains(response, "NoReverseMatch")

    def test_kpis_are_numbers(self):
        """KPIs deben mostrar números (aunque sean 0)"""
        response = self.client.get("/adminux/")

        # Verificar que el contexto contiene kpis
        self.assertIn("kpis", response.context)
        kpis = response.context["kpis"]

        # Verificar estructura de kpis
        self.assertIn("mesas", kpis)
        self.assertIn("productos", kpis)
        self.assertIn("pedidos", kpis)
        self.assertIn("caja", kpis)
        self.assertIn("reservas", kpis)
        self.assertIn("usuarios", kpis)

        # Verificar que los totales son números
        self.assertIsInstance(kpis["mesas"]["total"], int)
        self.assertIsInstance(kpis["productos"]["total"], int)
        self.assertIsInstance(kpis["pedidos"]["total"], int)

    def test_recent_data_structure(self):
        """Datos recientes deben tener la estructura correcta"""
        response = self.client.get("/adminux/")

        self.assertIn("recientes", response.context)
        recientes = response.context["recientes"]

        # Debe contener las tres secciones
        self.assertIn("pedidos", recientes)
        self.assertIn("transacciones", recientes)
        self.assertIn("reservas", recientes)

        # Cada sección debe ser iterable
        self.assertTrue(hasattr(recientes["pedidos"], "__iter__"))
        self.assertTrue(hasattr(recientes["transacciones"], "__iter__"))
        self.assertTrue(hasattr(recientes["reservas"], "__iter__"))

    def test_admin_home_link_present(self):
        """Debe haber link al admin nativo de Django"""
        response = self.client.get("/adminux/")

        self.assertIn("admin_home", response.context)
        self.assertEqual(response.context["admin_home"], "/admin/")
        self.assertContains(response, 'href="/admin/"')


class AdminUXCajaLinksTests(TestCase):
    """Tests específicos para los enlaces del módulo Caja"""

    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username="cajero_test",
            password="pass12345",
            is_staff=True,
            is_active=True,
            rol="Cajero"
        )
        self.client.login(username="cajero_test", password="pass12345")

    def test_caja_links_structure(self):
        """Verificar estructura de enlaces de Caja"""
        response = self.client.get("/adminux/")
        kpis = response.context["kpis"]

        # Verificar que tiene los contadores
        self.assertIn("transacciones", kpis["caja"])
        self.assertIn("cierres", kpis["caja"])

        # Verificar que tiene los enlaces (aunque sean '#')
        self.assertIn("alertas_list", kpis["caja"])
        self.assertIn("cierres_list", kpis["caja"])
        self.assertIn("transacciones_list", kpis["caja"])
        self.assertIn("detalles_pago_list", kpis["caja"])
        self.assertIn("historial_list", kpis["caja"])

    def test_caja_links_valid_or_hash(self):
        """Enlaces de Caja deben ser URLs válidas o '#'"""
        response = self.client.get("/adminux/")
        kpis = response.context["kpis"]["caja"]

        # Cada link debe ser string que empieza con '/' o es '#'
        for key in ["alertas_list", "cierres_list", "transacciones_list"]:
            link = kpis[key]
            self.assertTrue(
                link.startswith("/") or link == "#",
                f"Link {key} debe ser URL válida o '#', es: {link}"
            )
