# 🍽️ SGIR - Sistema de Gestión Integral para Restaurantes

Sistema profesional de gestión para restaurantes con autenticación QR, gestión de pedidos, control de caja, inventario en tiempo real y reportes avanzados.

[![Django](https://img.shields.io/badge/Django-5.1.4-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-10%2F10%20passing-brightgreen.svg)](restaurante_qr_project/README.md#-tests)
[![Version](https://img.shields.io/badge/Version-38.8-blue.svg)](restaurante_qr_project/README.md)
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
- **PIN (4 dígitos)**: Cajeros
- **QR (24h tokens)**: Meseros y cocineros
- **Rate limiting**: Protección contra fuerza bruta

### 💰 Módulos del Sistema
- **Caja**: Apertura/cierre de jornada, pagos mixtos, alertas de stock
- **Cocina**: Panel en tiempo real con actualización de estados
- **Mesero**: Gestión de pedidos y reservas de mesas
- **Cliente**: Menú QR sin registro, carrito interactivo
- **Reportes**: Dashboard con estadísticas y análisis de productos

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
│   ├── app/                     ← Apps (usuarios, pedidos, caja, etc.)
│   ├── backend/                 ← Configuración Django
│   ├── templates/               ← HTML/JS/CSS
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

### Implementaciones v38.8
- ✅ Rate limiting (5 intentos, 5 min bloqueo)
- ✅ CSRF protection (HttpOnly cookies)
- ✅ Tokens QR con expiración (24h)
- ✅ Validación dual de usuario activo
- ✅ Logging seguro (sin PINs/passwords)
- ✅ SECRET_KEY desde variables de entorno

### Producción
Ver [Configuración de Producción](restaurante_qr_project/README.md#️-configuración-de-producción) para:
- Configuración HTTPS
- PostgreSQL
- Gunicorn + Nginx
- Variables de entorno seguras

---

## 📈 Roadmap

- [x] Backend completo (Django + DRF)
- [x] Autenticación multi-modal
- [x] Sistema de tests (10/10)
- [x] Logging profesional
- [x] Rate limiting
- [ ] UI/UX moderna (Tailwind CSS)
- [ ] Dark mode
- [ ] Seguimiento de pedidos en tiempo real
- [ ] PWA completa con offline support
- [ ] WebSockets para notificaciones
- [ ] CI/CD con GitHub Actions

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

**Versión**: 38.8
**Última actualización**: 2025-01-11
**Estado**: ✅ **Backend Production Ready** | Tests: 10/10 | Logging: Profesional
**Próxima fase**: 🎨 Mejoras UI/UX

---

**Desarrollado con** ❤️ **usando Django + Python**
