"""
🚀 Script de Pruebas de Carga con Locust
Sistema Restaurante QR - CORREGIDO para arquitectura QR

Uso:
    locust -f locustfile.py --host=http://localhost:8000
    # Abrir: http://localhost:8089

Escenarios de prueba:
    1. CajeroUser: Login tradicional (usuario/contraseña)
    2. CocinaUser: Login con QR Token
    3. MeseroUser: Login con QR Token
    4. ClienteUser: Sin autenticación (QR de mesa)
"""

from locust import HttpUser, task, between, SequentialTaskSet
import json
import random


# ══════════════════════════════════════════════════════════════
# 🔧 CONFIGURACIÓN GLOBAL
# ══════════════════════════════════════════════════════════════

# ✅ CAJERO: Login tradicional con usuario/contraseña
CAJERO_CREDENTIALS = {
    "username": "cajero_test",
    "password": "Test123456"
}

# ✅ COCINERO: Login con QR Token (obtenido de base de datos)
COCINERO_QR_TOKEN = "896a7018-c438-43b3-bd74-748a872724c3"

# ✅ MESERO: Login con QR Token (obtenido de base de datos)
MESERO_QR_TOKEN = "810e325b-8f90-4315-8dee-59ecafd98fc6"


# ══════════════════════════════════════════════════════════════
# 🔐 UTILIDADES DE AUTENTICACIÓN
# ══════════════════════════════════════════════════════════════

class CajeroAuthUser(HttpUser):
    """
    Clase base para cajeros con login tradicional
    """
    abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.csrf_token = None

    def login(self, username, password):
        """Login tradicional con usuario/contraseña"""
        # Obtener CSRF token
        response = self.client.get("/login/")
        self.csrf_token = self.extract_csrf_token(response.text)

        # Realizar login
        login_data = {
            "username": username,
            "password": password,
            "csrfmiddlewaretoken": self.csrf_token
        }

        with self.client.post(
            "/usuarios/session-login/",
            data=login_data,
            headers={"Referer": f"{self.host}/login/"},
            catch_response=True,
            name="Iniciar sesión"
        ) as response:
            if response.status_code in [200, 302]:
                response.success()
                self.csrf_token = self.extract_csrf_token_from_cookie()
                return True
            else:
                response.failure(f"Login falló con estado {response.status_code}")
                return False

    def extract_csrf_token(self, html):
        """Extrae CSRF token del HTML"""
        import re
        match = re.search(r'name=["\']csrfmiddlewaretoken["\'] value=["\'](.*?)["\']', html)
        if match:
            return match.group(1)
        return None

    def extract_csrf_token_from_cookie(self):
        """Extrae CSRF token de las cookies"""
        return self.client.cookies.get('csrftoken')

    def get_headers(self):
        """Retorna headers con CSRF token"""
        return {
            "X-CSRFToken": self.csrf_token,
            "Content-Type": "application/json",
            "Referer": self.host
        }


class QRAuthUser(HttpUser):
    """
    Clase base para usuarios con login por QR (cocinero/mesero)
    """
    abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.csrf_token = None

    def login_qr(self, qr_token):
        """
        Login usando QR token (GET /qr-login/<token>/)
        Simula escanear un código QR
        """
        with self.client.get(
            f"/qr-login/{qr_token}/",
            allow_redirects=True,
            catch_response=True,
            name="Login QR"
        ) as response:
            if response.status_code == 200:
                response.success()
                # Extraer CSRF token de cookies
                self.csrf_token = self.client.cookies.get('csrftoken')
                return True
            else:
                response.failure(f"QR Login falló con estado {response.status_code}")
                return False

    def get_headers(self):
        """Retorna headers con CSRF token"""
        return {
            "X-CSRFToken": self.csrf_token if self.csrf_token else "",
            "Content-Type": "application/json",
            "Referer": self.host
        }


# ══════════════════════════════════════════════════════════════
# 💰 ESCENARIO 1: CAJERO - Procesamiento de Pagos
# ══════════════════════════════════════════════════════════════

class CajeroTaskSet(SequentialTaskSet):
    """
    Simula el flujo de trabajo de un cajero:
    1. Login tradicional
    2. Consultar mapa de mesas
    3. Ver pedidos pendientes
    4. Procesar pagos
    5. Consultar estadísticas
    """

    def on_start(self):
        """Login tradicional con usuario/contraseña"""
        success = self.user.login(
            CAJERO_CREDENTIALS["username"],
            CAJERO_CREDENTIALS["password"]
        )
        if not success:
            self.interrupt()

    @task(3)
    def consultar_mapa_mesas(self):
        """Consultar estado de las mesas"""
        self.client.get(
            "/api/caja/mapa-mesas/",
            headers=self.user.get_headers(),
            name="Mapa de Mesas"
        )

    @task(5)
    def consultar_dashboard(self):
        """Consultar estadísticas del dashboard"""
        self.client.get(
            "/api/caja/estadisticas/",
            headers=self.user.get_headers(),
            name="Dashboard - Estadísticas"
        )

    @task(2)
    def consultar_pedidos_pendientes(self):
        """Ver lista de pedidos pendientes de pago"""
        response = self.client.get(
            "/api/caja/pedidos/pendientes/",
            headers=self.user.get_headers(),
            name="Pedidos Pendientes"
        )

        if response.status_code == 200:
            try:
                data = response.json()
                if data.get("success") and data.get("pedidos"):
                    self.user.pedidos_disponibles = [p["id"] for p in data["pedidos"]]
            except:
                pass

    @task(1)
    def consultar_kanban(self):
        """Consultar tablero Kanban"""
        self.client.get(
            "/api/caja/pedidos/kanban/",
            headers=self.user.get_headers(),
            name="Kanban Board"
        )


class CajeroUser(CajeroAuthUser):
    """Usuario tipo Cajero (login tradicional)"""
    tasks = [CajeroTaskSet]
    wait_time = between(1, 3)


# ══════════════════════════════════════════════════════════════
# 👨‍🍳 ESCENARIO 2: COCINERO - Actualización de Estados
# ══════════════════════════════════════════════════════════════

class CocinaTaskSet(SequentialTaskSet):
    """
    Simula el flujo de trabajo de un cocinero:
    1. Login con QR Token
    2. Consultar pedidos pendientes en cocina
    3. Actualizar estados de pedidos
    """

    def on_start(self):
        """Login usando QR Token"""
        success = self.user.login_qr(COCINERO_QR_TOKEN)
        if not success:
            self.interrupt()

    @task(5)
    def consultar_pedidos_cocina(self):
        """Consultar pedidos en cola de cocina"""
        self.client.get(
            "/api/pedidos/cocina/",
            headers=self.user.get_headers(),
            name="Pedidos en Cocina"
        )

    @task(3)
    def actualizar_estado_kanban(self):
        """Actualizar estado de pedido en Kanban"""
        pedido_id = random.randint(1, 100)
        estados = ["pedido", "preparando", "listo", "entregado"]

        data = {
            "nuevo_estado": random.choice(estados)
        }

        with self.client.post(
            f"/api/caja/pedidos/{pedido_id}/cambiar-estado/",
            json=data,
            headers=self.user.get_headers(),
            catch_response=True,
            name="Actualizar Estado Kanban"
        ) as response:
            # Aceptar 200 (éxito) o 400 (pedido no existe)
            if response.status_code in [200, 400]:
                response.success()


class CocinaUser(QRAuthUser):
    """Usuario tipo Cocinero (login con QR)"""
    tasks = [CocinaTaskSet]
    wait_time = between(2, 5)


# ══════════════════════════════════════════════════════════════
# 🔔 ESCENARIO 3: MESERO - Consulta de Pedidos
# ══════════════════════════════════════════════════════════════

class MeseroTaskSet(SequentialTaskSet):
    """
    Simula el flujo de un mesero:
    1. Login con QR Token
    2. Consultar pedidos asignados
    3. Marcar pedidos como entregados
    """

    def on_start(self):
        """Login usando QR Token"""
        success = self.user.login_qr(MESERO_QR_TOKEN)
        if not success:
            self.interrupt()

    @task(5)
    def consultar_pedidos_mesero(self):
        """Consultar pedidos asignados"""
        self.client.get(
            "/api/pedidos/mesero/",
            headers=self.user.get_headers(),
            name="Pedidos del Mesero"
        )

    @task(2)
    def marcar_entregado(self):
        """Marcar pedido como entregado"""
        pedido_id = random.randint(1, 100)

        with self.client.post(
            f"/api/pedidos/{pedido_id}/entregar/",
            headers=self.user.get_headers(),
            catch_response=True,
            name="Marcar Pedido Entregado"
        ) as response:
            # Aceptar 200 (éxito) o 400 (pedido no existe)
            if response.status_code in [200, 400]:
                response.success()


class MeseroUser(QRAuthUser):
    """Usuario tipo Mesero (login con QR)"""
    tasks = [MeseroTaskSet]
    wait_time = between(3, 8)


# ══════════════════════════════════════════════════════════════
# 🍽️ ESCENARIO 4: CLIENTE - Creación de Pedidos
# ══════════════════════════════════════════════════════════════

class ClienteTaskSet(SequentialTaskSet):
    """
    Simula el flujo de un cliente:
    1. Consultar menú (sin autenticación)
    2. Ver productos disponibles
    """

    @task(5)
    def consultar_menu(self):
        """Consultar productos disponibles"""
        with self.client.get(
            "/api/productos/",
            catch_response=True,
            name="Consultar Menú"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("productos"):
                        self.user.productos_disponibles = data["productos"]
                    response.success()
                except:
                    response.success()


class ClienteUser(HttpUser):
    """Usuario tipo Cliente (no requiere autenticación)"""
    tasks = [ClienteTaskSet]
    wait_time = between(5, 15)


# ══════════════════════════════════════════════════════════════
# 📊 NOTAS DE USO
# ══════════════════════════════════════════════════════════════

"""
✅ ARQUITECTURA CORREGIDA:
- Cajero: Login tradicional (usuario/contraseña)
- Cocinero: Login con QR Token
- Mesero: Login con QR Token
- Cliente: Sin autenticación

🚀 COMANDOS DE PRUEBA:

1. Prueba Ligera (20 usuarios):
   locust -f locustfile.py --users 20 --spawn-rate 2 --run-time 2m

2. Prueba Media (50 usuarios):
   locust -f locustfile.py --users 50 --spawn-rate 5 --run-time 3m

3. Prueba de Estrés (100 usuarios):
   locust -f locustfile.py --users 100 --spawn-rate 10 --run-time 5m

📝 ANTES DE EJECUTAR:
1. Crear usuario de prueba: python crear_usuario_prueba.py
2. Verificar que el servidor Django esté corriendo
3. Abrir http://localhost:8089 en el navegador
"""
