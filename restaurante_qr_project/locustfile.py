"""
🚀 Script de Pruebas de Carga con Locust
Sistema Restaurante QR - Módulo de Caja

Uso:
    locust -f locustfile.py --host=http://localhost:8000

    # Con interfaz web (recomendado)
    locust -f locustfile.py --host=http://localhost:8000
    # Abrir: http://localhost:8089

    # Modo headless (sin interfaz)
    locust -f locustfile.py --host=http://localhost:8000 --users 10 --spawn-rate 2 --run-time 1m --headless

Escenarios de prueba:
    1. CajeroUser: Simula cajeros procesando pagos
    2. CocinaUser: Simula cocineros actualizando estados
    3. ClienteUser: Simula clientes haciendo pedidos
    4. MeseroUser: Simula meseros consultando pedidos
"""

from locust import HttpUser, task, between, SequentialTaskSet
import json
import random


# ══════════════════════════════════════════════════════════════
# 🔧 CONFIGURACIÓN GLOBAL
# ══════════════════════════════════════════════════════════════

# Credenciales de prueba (crear estos usuarios en el sistema)
CAJERO_CREDENTIALS = {
    "username": "cajero_test",
    "password": "Test123456"
}

COCINERO_CREDENTIALS = {
    "username": "cocinero_test",
    "password": "Test123456"
}

MESERO_CREDENTIALS = {
    "username": "mesero_test",
    "password": "Test123456"
}


# ══════════════════════════════════════════════════════════════
# 🔐 UTILIDADES DE AUTENTICACIÓN
# ══════════════════════════════════════════════════════════════

class AuthenticatedUser(HttpUser):
    """
    Clase base para usuarios autenticados
    Maneja login y extracción de CSRF token
    """
    abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.csrf_token = None
        self.session_cookie = None

    def login(self, username, password):
        """
        Realiza login y extrae CSRF token
        """
        # Obtener CSRF token de la página de login
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
            name="Login"
        ) as response:
            if response.status_code == 200 or response.status_code == 302:
                response.success()
                # Extraer nuevo CSRF token después del login
                self.csrf_token = self.extract_csrf_token_from_cookie()
                return True
            else:
                response.failure(f"Login falló con status {response.status_code}")
                return False

    def extract_csrf_token(self, html):
        """
        Extrae CSRF token del HTML
        """
        import re
        match = re.search(r'name=["\']csrfmiddlewaretoken["\'] value=["\'](.*?)["\']', html)
        if match:
            return match.group(1)
        return None

    def extract_csrf_token_from_cookie(self):
        """
        Extrae CSRF token de las cookies
        """
        return self.client.cookies.get('csrftoken')

    def get_headers(self):
        """
        Retorna headers con CSRF token
        """
        return {
            "X-CSRFToken": self.csrf_token,
            "Content-Type": "application/json",
            "Referer": self.host
        }


# ══════════════════════════════════════════════════════════════
# 💰 ESCENARIO 1: CAJERO - Procesamiento de Pagos
# ══════════════════════════════════════════════════════════════

class CajeroTaskSet(SequentialTaskSet):
    """
    Simula el flujo de trabajo de un cajero:
    1. Login
    2. Consultar mapa de mesas
    3. Ver lista de pedidos pendientes
    4. Procesar pagos
    5. Consultar estadísticas
    """

    def on_start(self):
        """Ejecutar al inicio: Login"""
        success = self.user.login(
            CAJERO_CREDENTIALS["username"],
            CAJERO_CREDENTIALS["password"]
        )
        if not success:
            self.interrupt()

    @task(1)
    def consultar_dashboard(self):
        """Consultar estadísticas del dashboard"""
        with self.client.get(
            "/api/caja/estadisticas/",
            headers=self.user.get_headers(),
            name="Dashboard - Estadísticas"
        ) as response:
            if response.status_code == 200:
                response.success()

    @task(3)
    def consultar_mapa_mesas(self):
        """Consultar estado de las mesas"""
        with self.client.get(
            "/api/caja/mapa-mesas/",
            headers=self.user.get_headers(),
            name="Mapa de Mesas"
        ) as response:
            if response.status_code == 200:
                response.success()

    @task(2)
    def consultar_pedidos_pendientes(self):
        """Ver lista de pedidos pendientes de pago"""
        with self.client.get(
            "/api/caja/pedidos/pendientes/",
            headers=self.user.get_headers(),
            name="Pedidos Pendientes"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                # Guardar IDs de pedidos para usarlos en pagos
                if data.get("success") and data.get("pedidos"):
                    self.user.pedidos_disponibles = [p["id"] for p in data["pedidos"]]
                response.success()

    @task(5)
    def procesar_pago_simple(self):
        """Simular procesamiento de pago"""
        # Verificar si hay pedidos disponibles
        if not hasattr(self.user, 'pedidos_disponibles') or not self.user.pedidos_disponibles:
            return

        pedido_id = random.choice(self.user.pedidos_disponibles)
        metodos_pago = ["efectivo", "tarjeta", "qr"]

        pago_data = {
            "pedido_id": pedido_id,
            "metodo_pago": random.choice(metodos_pago),
            "monto_recibido": round(random.uniform(50, 500), 2)
        }

        with self.client.post(
            "/api/caja/pago/simple/",
            json=pago_data,
            headers=self.user.get_headers(),
            name="Procesar Pago Simple"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    response.success()
                else:
                    response.failure(f"Pago rechazado: {data.get('error')}")

    @task(1)
    def consultar_kanban(self):
        """Consultar tablero Kanban"""
        with self.client.get(
            "/api/caja/pedidos/kanban/",
            headers=self.user.get_headers(),
            name="Kanban Board"
        ) as response:
            if response.status_code == 200:
                response.success()


class CajeroUser(AuthenticatedUser):
    """Usuario tipo Cajero"""
    tasks = [CajeroTaskSet]
    wait_time = between(1, 3)  # Espera entre 1-3 segundos entre tareas


# ══════════════════════════════════════════════════════════════
# 👨‍🍳 ESCENARIO 2: COCINERO - Actualización de Estados
# ══════════════════════════════════════════════════════════════

class CocinaTaskSet(SequentialTaskSet):
    """
    Simula el flujo de trabajo de un cocinero:
    1. Login
    2. Consultar pedidos pendientes en cocina
    3. Actualizar estados de pedidos en Kanban
    """

    def on_start(self):
        """Ejecutar al inicio: Login"""
        success = self.user.login(
            COCINERO_CREDENTIALS["username"],
            COCINERO_CREDENTIALS["password"]
        )
        if not success:
            self.interrupt()

    @task(5)
    def consultar_pedidos_cocina(self):
        """Consultar pedidos en cola de cocina"""
        with self.client.get(
            "/api/pedidos/cocina/",
            headers=self.user.get_headers(),
            name="Pedidos en Cocina"
        ) as response:
            if response.status_code == 200:
                response.success()

    @task(3)
    def actualizar_estado_kanban(self):
        """Actualizar estado de pedido en Kanban"""
        # Simulación: cambiar estado aleatorio
        pedido_id = random.randint(1, 100)
        estados = ["pedido", "preparando", "listo", "entregado"]

        data = {
            "nuevo_estado": random.choice(estados)
        }

        with self.client.post(
            f"/api/caja/pedidos/{pedido_id}/cambiar-estado/",
            json=data,
            headers=self.user.get_headers(),
            name="Actualizar Estado Kanban"
        ) as response:
            # Aceptar 200 (éxito) o 400 (pedido no existe)
            if response.status_code in [200, 400]:
                response.success()


class CocinaUser(AuthenticatedUser):
    """Usuario tipo Cocinero"""
    tasks = [CocinaTaskSet]
    wait_time = between(2, 5)  # Espera entre 2-5 segundos entre tareas


# ══════════════════════════════════════════════════════════════
# 🍽️ ESCENARIO 3: CLIENTE - Creación de Pedidos
# ══════════════════════════════════════════════════════════════

class ClienteTaskSet(SequentialTaskSet):
    """
    Simula el flujo de un cliente:
    1. Consultar menú
    2. Crear pedido
    3. Confirmar pedido
    """

    @task(2)
    def consultar_menu(self):
        """Consultar productos disponibles"""
        with self.client.get(
            "/api/productos/",
            name="Consultar Menú"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("productos"):
                    self.user.productos_disponibles = data["productos"]
                response.success()

    @task(5)
    def crear_pedido_cliente(self):
        """Crear un nuevo pedido desde QR"""
        if not hasattr(self.user, 'productos_disponibles') or not self.user.productos_disponibles:
            return

        # Seleccionar 1-5 productos aleatorios
        num_productos = random.randint(1, 5)
        productos_seleccionados = random.sample(
            self.user.productos_disponibles,
            min(num_productos, len(self.user.productos_disponibles))
        )

        pedido_data = {
            "mesa_numero": random.randint(1, 20),
            "productos": [
                {
                    "id": p["id"],
                    "cantidad": random.randint(1, 5)
                }
                for p in productos_seleccionados
            ],
            "observaciones": "Pedido de prueba Locust"
        }

        with self.client.post(
            "/api/pedidos/cliente/crear/",
            json=pedido_data,
            headers={"Content-Type": "application/json"},
            name="Crear Pedido Cliente"
        ) as response:
            if response.status_code == 200:
                response.success()


class ClienteUser(HttpUser):
    """Usuario tipo Cliente (no requiere autenticación)"""
    tasks = [ClienteTaskSet]
    wait_time = between(5, 15)  # Clientes tardan más entre acciones


# ══════════════════════════════════════════════════════════════
# 👔 ESCENARIO 4: MESERO - Consulta de Pedidos
# ══════════════════════════════════════════════════════════════

class MeseroTaskSet(SequentialTaskSet):
    """
    Simula el flujo de un mesero:
    1. Login
    2. Consultar pedidos asignados
    3. Marcar pedidos como entregados
    """

    def on_start(self):
        """Ejecutar al inicio: Login"""
        success = self.user.login(
            MESERO_CREDENTIALS["username"],
            MESERO_CREDENTIALS["password"]
        )
        if not success:
            self.interrupt()

    @task(5)
    def consultar_pedidos_mesero(self):
        """Consultar pedidos asignados"""
        with self.client.get(
            "/api/pedidos/mesero/",
            headers=self.user.get_headers(),
            name="Pedidos del Mesero"
        ) as response:
            if response.status_code == 200:
                response.success()

    @task(2)
    def marcar_entregado(self):
        """Marcar pedido como entregado"""
        pedido_id = random.randint(1, 100)

        with self.client.post(
            f"/api/pedidos/{pedido_id}/entregar/",
            headers=self.user.get_headers(),
            name="Marcar Pedido Entregado"
        ) as response:
            # Aceptar 200 (éxito) o 400 (pedido no existe)
            if response.status_code in [200, 400]:
                response.success()


class MeseroUser(AuthenticatedUser):
    """Usuario tipo Mesero"""
    tasks = [MeseroTaskSet]
    wait_time = between(3, 8)  # Espera entre 3-8 segundos entre tareas


# ══════════════════════════════════════════════════════════════
# 🎯 CONFIGURACIÓN DE ESCENARIOS
# ══════════════════════════════════════════════════════════════

"""
Para ejecutar diferentes escenarios, comenta/descomenta las clases:

# Prueba de Carga en Caja (recomendado)
- Usuarios: 10-50 cajeros
- Duración: 5-10 minutos
- Comando: locust -f locustfile.py --host=http://localhost:8000 --users 20 --spawn-rate 2 --run-time 5m

# Prueba de Estrés en Cocina
- Usuarios: 5-20 cocineros
- Duración: 3-5 minutos
- Comando: locust -f locustfile.py --host=http://localhost:8000 --users 10 --spawn-rate 1 --run-time 3m

# Prueba de Pico de Clientes
- Usuarios: 50-200 clientes
- Duración: 10-15 minutos
- Comando: locust -f locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 10m

# Prueba Mixta (recomendado para producción)
- 10 cajeros + 5 cocineros + 30 clientes + 5 meseros
- Duración: 15-30 minutos
- Comando: locust -f locustfile.py --host=http://localhost:8000 --users 50 --spawn-rate 5 --run-time 15m
"""


# ══════════════════════════════════════════════════════════════
# 📊 MÉTRICAS A MONITOREAR
# ══════════════════════════════════════════════════════════════

"""
Durante las pruebas, monitorear:

1. Response Times:
   - Percentil 50 (mediana): < 200ms
   - Percentil 95: < 500ms
   - Percentil 99: < 1000ms

2. Requests per Second (RPS):
   - Objetivo: > 100 RPS
   - Crítico: < 50 RPS

3. Failure Rate:
   - Objetivo: < 1%
   - Crítico: > 5%

4. Recursos del Servidor:
   - CPU: < 80%
   - RAM: < 80%
   - Conexiones DB: < límite configurado

5. Endpoints Críticos:
   - /api/caja/pago/simple/ (más importante)
   - /api/caja/mapa-mesas/
   - /api/pedidos/cliente/crear/
"""
