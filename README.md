# 🍽️ SGIR – Sistema de Gestión Integral para Restaurantes

SGIR es un sistema web profesional para la gestión operativa de restaurantes, desarrollado con **Django 5** y **PostgreSQL**, preparado para ejecutarse en entornos **Docker** tanto en desarrollo como en producción.

El sistema cubre los flujos reales de un restaurante: pedidos, caja, inventario, reservas, usuarios y reportes, con paneles diferenciados por rol.

---

## 🚀 Funcionalidades Principales

- Gestión completa de **pedidos** con estados (creado, en preparación, listo, entregado, cerrado)
- **Caja** con jornadas laborales y control de ingresos/egresos
- **Inventario** con descuento automático de stock
- **Reservas de mesas** y control de disponibilidad
- **Usuarios con roles**: Administrador, Cajero, Mesero, Cocinero, Cliente
- **Menú digital** accesible vía QR
- **Reportes** en PDF y Excel
- Panel administrativo basado en Django Admin

---

## 🧠 Arquitectura del Sistema

El proyecto está organizado de forma modular siguiendo buenas prácticas de Django.

```
restaurante_qr_project/
├── app/                    # Apps del negocio
│   ├── usuarios/           # Usuarios y roles
│   ├── pedidos/            # Pedidos y estados
│   ├── productos/          # Productos y categorías
│   ├── mesas/              # Mesas del restaurante
│   ├── reservas/           # Reservas
│   ├── caja/               # Caja y transacciones
│   ├── inventario/         # Stock
│   ├── reportes/           # Reportes
│   └── configuracion/      # Configuración general
├── backend/                # Settings, URLs, WSGI
├── templates/              # Templates HTML
├── static/                 # CSS, JS e imágenes
├── manage.py
├── Dockerfile
├── docker-compose.yml      # Desarrollo
├── docker-compose.prod.yml # Producción
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🛠️ Stack Tecnológico

### Backend
- Python 3.12
- Django 5.1
- Django REST Framework
- PostgreSQL 16

### Frontend
- HTML5 / CSS3
- JavaScript (Vanilla)
- Compatible con PWA

### Infraestructura
- Docker & Docker Compose
- Gunicorn (producción)
- Nginx recomendado como reverse proxy

---

## ⚙️ Requisitos

### Desarrollo / Producción
- Docker 24+
- Docker Compose 2+
- Git

*(No es necesario instalar Python ni PostgreSQL localmente si usas Docker)*

---

## 🔐 Variables de Entorno

El proyecto utiliza variables de entorno para seguridad.

### Archivo de ejemplo
```
.env.example
```

### Archivos reales (NO se suben a Git)
- `.env`
- `.env.docker`

Estos archivos están protegidos por `.gitignore`.

---

## 🚀 Instalación con Docker (Recomendado)

### 1️⃣ Clonar el repositorio
```bash
git clone https://github.com/KaradyGamer/Sistema-de-Gesti-n-Integral-para-Restaurantes-SGIR-.git
cd restaurante_qr_project
```

### 2️⃣ Configurar variables de entorno

```bash
cp .env.example .env.docker
```

Editar `.env.docker` y configurar:

```env
SECRET_KEY=tu_secret_key_segura
DEBUG=True
POSTGRES_DB=sgir
POSTGRES_USER=sgir_user
POSTGRES_PASSWORD=password_seguro
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

### 3️⃣ Levantar el sistema

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

### 4️⃣ Aplicar migraciones

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
```

### 5️⃣ Crear usuario administrador

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

---

## 🌐 Acceso al Sistema

Una vez levantado el sistema:

- **Admin**: http://127.0.0.1:8000/admin/
- **Caja**: http://127.0.0.1:8000/caja/
- **Cocina**: http://127.0.0.1:8000/cocina/
- **Mesero**: http://127.0.0.1:8000/mesero/
- **Menú QR (clientes)**: http://127.0.0.1:8000/menu/
- **Healthcheck**: http://127.0.0.1:8000/health/

---

## 📦 Uso Básico

1. Crear usuarios desde el panel de administración
2. Asignar roles (cajero, mesero, cocinero, etc.)
3. Crear mesas y productos
4. Abrir jornada de caja
5. Tomar pedidos, preparar, cobrar y cerrar

---

## 📂 Archivos que NO deben estar en el repositorio

Por seguridad, estos archivos **NO se suben a Git**:

- `.env`
- `.env.docker`
- `data/`
- `logs/`
- `db.sqlite3`
- Backups de base de datos

El repositorio solo contiene código y configuración segura.

---

## 🧪 Auditoría y Verificación

El sistema incluye scripts de auditoría para verificar:

- Estado de contenedores
- Conectividad
- Migraciones
- Base de datos
- Logs
- ORM

*(Opcional, para validación técnica)*

---

## 🔒 Producción (Recomendaciones)

Para un entorno productivo real:

```env
DEBUG=False
ALLOWED_HOSTS=tudominio.com,www.tudominio.com
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

Usar Nginx como reverse proxy y HTTPS.

---

## 📄 Licencia

Proyecto privado.
Uso académico y demostrativo.

---

## 📅 Estado del Proyecto

- **Backend**: Estable
- **Docker**: Configurado y validado
- **Base de datos**: PostgreSQL
- **Estado general**: **Listo para uso y despliegue**

---

**SGIR – Sistema de Gestión Integral para Restaurantes**
