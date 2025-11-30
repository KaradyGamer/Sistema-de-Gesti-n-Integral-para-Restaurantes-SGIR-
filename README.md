# 🍽️ SGIR - Sistema de Gestión Integral para Restaurantes

Sistema profesional de gestión para restaurantes con autenticación QR, gestión de pedidos, control de caja, inventario en tiempo real y panel AdminUX unificado.

[![Django](https://img.shields.io/badge/Django-5.1.4-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-10%2F10%20passing-brightgreen.svg)](restaurante_qr_project/README.md#-tests)
[![Version](https://img.shields.io/badge/Version-39.5-blue.svg)](restaurante_qr_project/README.md)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success.svg)](#)

---

## 🚀 Inicio Rápido

```bash
# 1. Clonar repositorio
git clone https://github.com/KaradyGamer/Sistema-de-Gesti-n-Integral-para-Restaurantes-SGIR-.git
cd ProyectoR/restaurante_qr_project

# 2. Crear entorno virtual e instalar dependencias
python -m venv env
env\Scripts\activate  # Windows
pip install -r requirements.txt

# 3. Configurar variables de entorno
copy .env.example .env
# Editar .env con SECRET_KEY segura

# 4. Inicializar base de datos
python manage.py migrate
python scripts/crear_datos_iniciales.py  # Solo desarrollo

# 5. Iniciar servidor
python manage.py runserver
```

**Acceder a**: http://127.0.0.1:8000/

---

## ✨ Características Principales

### 🔐 Autenticación Multi-Modal
- **Password**: Administradores
- **PIN (4-6 dígitos)**: Cajeros con campo dedicado
- **QR (24h tokens)**: Meseros y cocineros con generación bajo demanda
- **Rate limiting**: Protección contra fuerza bruta

### 💼 AdminUX - Panel Unificado (v39.5)
- **Dashboard**: Visualización en tiempo real de KPIs, gráficas de pedidos y ventas
- **Mesas**: Gestión completa con zonas, capacidad y estados
- **Productos**: CRUD con categorías, imágenes y gestión de stock
- **Pedidos**: Lista y detalle de todos los pedidos
- **Reservas**: Sistema de reservas con calendario
- **Usuarios**: Gestión completa con PIN y generación de QR
- **Inventario**: Sistema completo de insumos con alertas de stock bajo
  - Categorías de insumos
  - Control de movimientos (entrada/salida/ajuste)
  - Alertas automáticas de stock mínimo
- **Configuración**: Parámetros del sistema (negocio, financiero, horarios, tickets)
- **Reportes**: Análisis de ventas y productos más vendidos

### 🎨 UI/UX Moderna
- **Diseño Dark Theme**: Interface oscura profesional con variables CSS
- **Sidebar vertical**: Navegación lateral con iconos Boxicons
- **Topbar responsive**: Breadcrumbs y dropdown de usuario
- **Loader animado**: Transiciones suaves entre páginas
- **Templates base**: `base_list.html` y `base_form.html` unificados
- **Estilos del prototipo**: Integrados desde `/Prototipo/adminux/`

### 💰 Módulos del Sistema
- **Caja**: Apertura/cierre de jornada, pagos mixtos, alertas de stock
- **Cocina**: Panel en tiempo real con actualización de estados
- **Mesero**: Gestión de pedidos y reservas de mesas
- **Cliente**: Menú QR sin registro, carrito interactivo

### ✅ Calidad del Código
- **Tests**: 10/10 pasando (autenticación, rate limiting, jornada)
- **Logging**: Sistema profesional estructurado (0 print statements)
- **Seguridad**: CSRF, tokens seguros, validación dual de usuarios
- **Documentación**: README completo con guías de instalación y producción

---

## 📚 Documentación Completa

👉 **[Ver Documentación Técnica Completa](restaurante_qr_project/README.md)**

Incluye:
- Instalación detallada paso a paso
- Estructura del proyecto explicada
- Guía de seguridad y producción
- Tests y coverage
- Resolución de problemas
- Scripts de utilidad

---

## 🧪 Tests

```bash
# Ejecutar todos los tests
python manage.py test

# Tests específicos
python manage.py test app.usuarios.tests.test_auth
```

**Estado actual**: ✅ **10/10 tests pasando**
- Autenticación (QR, PIN, Password)
- Rate limiting
- Tokens QR (expiración, un solo uso)
- Usuario inactivo (validación dual)

---

## 🛠️ Stack Tecnológico

| Categoría | Tecnología |
|-----------|-----------|
| **Backend** | Django 5.1.4 + DRF 3.16+ |
| **Base de Datos** | SQLite (dev) / PostgreSQL (prod) |
| **Frontend** | HTML5 + CSS3 + JavaScript Vanilla |
| **UI Framework** | Custom CSS con variables (Dark Theme) |
| **Iconos** | Boxicons 2.1.4 |
| **Gráficos** | Chart.js |
| **Seguridad** | Rate limiting, CSRF, JWT tokens |
| **Logging** | Python logging module |
| **Tests** | Django TestCase + Coverage |

---

## 📁 Estructura del Proyecto

```
ProyectoR/
│
├── restaurante_qr_project/      ← Proyecto Django principal
│   ├── app/                     ← Apps Django
│   │   ├── adminux/             ← Panel administrativo unificado
│   │   ├── caja/                ← Módulo de caja
│   │   ├── cliente/             ← Módulo de clientes (menú QR)
│   │   ├── cocinero/            ← Panel de cocina
│   │   ├── configuracion/       ← Configuración del sistema (v39.4)
│   │   ├── inventario/          ← Gestión de insumos (v39.4)
│   │   ├── mesero/              ← Panel de meseros
│   │   ├── pedidos/             ← Gestión de pedidos
│   │   └── usuarios/            ← Autenticación y usuarios
│   │
│   ├── backend/                 ← Configuración Django
│   ├── templates/               ← HTML/JS/CSS
│   │   ├── css/adminux/         ← Estilos AdminUX
│   │   │   ├── main.css         ← Estilos principales (2412 líneas)
│   │   │   └── prototipo-vars.css
│   │   ├── html/adminux/        ← Templates AdminUX
│   │   │   ├── base_adminux.html      ← Layout base
│   │   │   ├── base_list.html         ← Base para listados
│   │   │   ├── base_form.html         ← Base para formularios
│   │   │   ├── dashboard.html
│   │   │   ├── configuracion.html
│   │   │   ├── components/
│   │   │   │   ├── sidebar.html       ← Sidebar unificado
│   │   │   │   └── topbar.html        ← Topbar unificado
│   │   │   ├── inventario/            ← Templates de inventario
│   │   │   ├── mesas/
│   │   │   ├── pedidos/
│   │   │   ├── productos/
│   │   │   ├── reservas/
│   │   │   └── usuarios/
│   │   └── js/adminux/          ← JavaScript AdminUX
│   │       ├── main.js          ← Lógica principal
│   │       └── loader.js        ← Loader de navegación
│   │
│   ├── static/                  ← Archivos estáticos
│   ├── scripts/                 ← Scripts de utilidad
│   ├── logs/                    ← Logs de aplicación
│   ├── manage.py
│   ├── requirements.txt
│   └── README.md                ← Documentación técnica completa
│
├── .gitignore
└── README.md                    ← Este archivo
```

---

## 🔒 Seguridad

### Implementaciones v39.5
- ✅ Rate limiting (5 intentos, 5 min bloqueo)
- ✅ CSRF protection (HttpOnly cookies)
- ✅ Tokens QR con expiración (24h)
- ✅ Validación dual de usuario activo
- ✅ Logging seguro (sin PINs/passwords)
- ✅ SECRET_KEY desde variables de entorno
- ✅ PIN de 4-6 dígitos para cajeros
- ✅ Generación de QR bajo demanda para usuarios

### Producción
Ver [Configuración de Producción](restaurante_qr_project/README.md#️-configuración-de-producción) para:
- Configuración HTTPS
- PostgreSQL
- Gunicorn + Nginx
- Variables de entorno seguras

---

## 📈 Changelog v39.5

### ✨ Nuevas Características
- **Inventario completo**: Sistema de gestión de insumos con categorías, movimientos y alertas
- **Configuración del sistema**: Parámetros centralizados (negocio, financiero, horarios, tickets)
- **PIN para usuarios**: Campo dedicado de 4-6 dígitos para cajeros
- **Generación de QR**: API para generar tokens QR bajo demanda para meseros/cocineros
- **Sidebar actualizado**: Nuevas entradas para Inventario, Reportes y Configuración

### 🎨 Mejoras UI/UX
- **Unificación visual**: Integración completa del diseño del prototipo
- **Templates base**: `base_list.html` y `base_form.html` con estructura consistente
- **Clases CSS corregidas**: Removido sufijo `-premium` de todas las clases
- **Loader suave**: Animación de carga entre navegación de páginas
- **Dark theme**: Variables CSS con tema oscuro profesional

### 🐛 Correcciones
- Corregidas clases CSS en sidebar y topbar (removido `-premium`)
- Eliminado error `toggleDark is not defined` en consola
- Limpieza de archivos obsoletos (`base_adminux_old.html`, `dashboard-premium_old.css`)

### 🧹 Limpieza
- Eliminados archivos innecesarios (`nul`, carpeta `Prototipo/`)
- Limpiados caches de Python (`__pycache__`)
- Removidos archivos estáticos no utilizados

---

## 🐛 Soporte

Para problemas, consultar:
1. [Resolución de Problemas](restaurante_qr_project/README.md#-resolución-de-problemas)
2. [Issues en GitHub](https://github.com/KaradyGamer/Sistema-de-Gesti-n-Integral-para-Restaurantes-SGIR-/issues)

---

## 📄 Licencia

Este proyecto es privado y confidencial. Todos los derechos reservados.

---

## 🏆 Estado del Proyecto

**Versión**: 39.5
**Última actualización**: 2025-01-30
**Estado**: ✅ **Production Ready** | Tests: 10/10 | UI: Modernizada
**Próxima fase**: 🎨 Migración de vistas existentes a templates unificados

---

**Desarrollado con** ❤️ **usando Django + Python**
