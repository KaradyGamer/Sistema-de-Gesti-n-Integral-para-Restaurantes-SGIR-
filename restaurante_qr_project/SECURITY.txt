# 🔒 SECURITY.md - SGIR Backend

**Proyecto:** Sistema de Gestión Integral para Restaurantes (SGIR)
**Versión:** 1.0.0
**Última actualización:** 2025-01-02

---

## 📋 Índice

1. [Políticas de Seguridad](#políticas-de-seguridad)
2. [Configuración Segura](#configuración-segura)
3. [Autenticación y Autorización](#autenticación-y-autorización)
4. [Protección de Datos](#protección-de-datos)
5. [Hardening Django](#hardening-django)
6. [Gestión de Secretos](#gestión-de-secretos)
7. [Logging y Monitoreo](#logging-y-monitoreo)
8. [Reporte de Vulnerabilidades](#reporte-de-vulnerabilidades)
9. [Checklist de Seguridad](#checklist-de-seguridad)

---

## 🛡️ Políticas de Seguridad

### Versiones Soportadas

| Versión | Soporte          |
|---------|------------------|
| 1.0.x   | ✅ Sí            |
| < 1.0   | ❌ No            |

### Ciclo de Actualizaciones

- **Parches de seguridad:** Inmediato (< 24h)
- **Actualizaciones menores:** Mensual
- **Actualizaciones mayores:** Trimestral

---

## ⚙️ Configuración Segura

### Variables de Entorno Obligatorias

```bash
# CRÍTICO: Generar nueva SECRET_KEY
SECRET_KEY=<generar-con-get_random_secret_key>

# PRODUCCIÓN: Siempre False
DEBUG=False

# PRODUCCIÓN: Especificar dominios exactos
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com

# PostgreSQL: Credenciales únicas
POSTGRES_DB=sgir_prod
POSTGRES_USER=sgir_prod_user
POSTGRES_PASSWORD=<password-fuerte-aleatorio>
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

### Generar SECRET_KEY Segura

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Requisitos:**
- Mínimo 50 caracteres
- Única por entorno
- Nunca reutilizar
- Rotar cada 90 días en producción

---

## 🔐 Autenticación y Autorización

### Endpoints Protegidos

**Todos los endpoints críticos requieren:**
- `IsAuthenticated` (DRF)
- `@login_required` (Django views)
- Decoradores personalizados según rol

### Endpoints Públicos Permitidos

| Endpoint | Método | Justificación |
|----------|--------|---------------|
| `/` | GET | Formulario cliente |
| `/health/` | GET | Healthcheck cloud |
| `/api/mesas/` | GET | Consulta mesas disponibles |

**TODOS los demás endpoints están protegidos.**

### JWT Configuration

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=14),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}
```

### Roles y Permisos

| Rol | Permisos |
|-----|----------|
| `superuser` | Acceso total (Django Admin) |
| `cajero` | Caja, transacciones, pedidos |
| `mesero` | Pedidos, mesas, QR login |
| `cocinero` | Pedidos en cocina, QR login |
| `cliente` | Solo lectura mesas/productos |

---

## 🗄️ Protección de Datos

### Datos Sensibles

**NUNCA almacenar en texto plano:**
- Contraseñas (usar `make_password()`)
- Tokens de sesión
- Información de pago

**Datos protegidos:**
- Información personal (GDPR/LOPD)
- Transacciones financieras
- Registros de auditoría

### CORS y CSRF

```python
# Producción
CORS_ALLOWED_ORIGINS = [
    "https://tu-dominio.com",
]

CSRF_TRUSTED_ORIGINS = [
    "https://tu-dominio.com",
]

# Deshabilitar en producción
CORS_ALLOW_ALL_ORIGINS = False
```

---

## 🔨 Hardening Django

### Settings de Seguridad (Producción)

```python
# HTTPS obligatorio
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Headers de seguridad
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Proxy headers (detrás de Nginx/Traefik)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

### Configuración de Sesión

```python
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 3600  # 1 hora
```

---

## 🔑 Gestión de Secretos

### NUNCA Commitear

❌ `.env`
❌ `local_settings.py`
❌ Credenciales de BD
❌ API keys
❌ Certificados SSL/TLS

### Archivo .gitignore Verificado

```bash
# Verificar que .env esté ignorado
git check-ignore .env
# Output esperado: .env

# Verificar historial (CRÍTICO)
git log --all --full-history -- .env
# Output esperado: vacío (nunca fue commiteado)
```

### Rotación de Secretos

**Frecuencia recomendada:**
- `SECRET_KEY`: Cada 90 días
- Contraseñas de BD: Cada 180 días
- JWT tokens: Automático (14 días)
- API keys externas: Según proveedor

---

## 📊 Logging y Monitoreo

### Eventos Loggeados

**Siempre logear:**
- ✅ Login exitoso/fallido
- ✅ Cambios en permisos
- ✅ Acceso a endpoints críticos
- ✅ Errores de autenticación
- ✅ Intentos de acceso no autorizado

**Ejemplo:**
```python
import logging
logger = logging.getLogger(__name__)

logger.warning(f"Login fallido: {username} desde {ip}")
logger.info(f"Pedido creado: ID={pedido.id} por {user}")
```

### Integración con Servicios Cloud

**Recomendados:**
- Sentry (errores y excepciones)
- Datadog / New Relic (APM)
- CloudWatch / Stackdriver (logs centralizados)

---

## 🚨 Reporte de Vulnerabilidades

### Proceso de Reporte

Si descubres una vulnerabilidad de seguridad:

1. **NO abrir issue público**
2. Enviar reporte privado a: `security@tu-dominio.com`
3. Incluir:
   - Descripción de la vulnerabilidad
   - Pasos para reproducir
   - Impacto potencial
   - Sugerencia de solución (opcional)

### Tiempo de Respuesta

- **Reconocimiento:** < 48 horas
- **Evaluación:** < 7 días
- **Parche:** < 30 días (crítico: < 7 días)

---

## ✅ Checklist de Seguridad

### Pre-Despliegue

- [ ] `DEBUG=False` en producción
- [ ] `SECRET_KEY` única y generada aleatoriamente
- [ ] `ALLOWED_HOSTS` configurado correctamente
- [ ] HTTPS habilitado
- [ ] Certificado SSL válido
- [ ] HSTS configurado
- [ ] `.env` no está en Git
- [ ] Credenciales de BD rotadas
- [ ] CORS configurado restrictivamente
- [ ] CSRF protección activada
- [ ] Logs centralizados configurados
- [ ] Backups automáticos activos

### Post-Despliegue

- [ ] Healthcheck responde correctamente
- [ ] Logs sin errores críticos
- [ ] Endpoints públicos verificados
- [ ] JWT expira correctamente
- [ ] Rate limiting activo (si aplica)
- [ ] Monitoreo de errores activo
- [ ] Alertas configuradas

### Auditoría Periódica

**Mensual:**
- [ ] Revisar logs de acceso
- [ ] Actualizar dependencias
- [ ] Verificar certificados SSL

**Trimestral:**
- [ ] Rotar SECRET_KEY
- [ ] Auditoría de permisos
- [ ] Revisión de código

**Anual:**
- [ ] Pentesting externo
- [ ] Auditoría completa de seguridad
- [ ] Actualización de políticas

---

## 📚 Referencias

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Django Security](https://docs.djangoproject.com/en/5.1/topics/security/)
- [DRF Security](https://www.django-rest-framework.org/topics/security/)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/security.html)

---

## 📝 Changelog de Seguridad

### [1.0.0] - 2025-01-02

**Añadido:**
- Hardening completo de Django
- Logging contextual en todos los módulos
- Eliminación de bare except (E722)
- Documentación de seguridad

**Corregido:**
- Remoción de .env del tracking Git
- Variables no usadas (F841)
- Configuración CORS restrictiva

---

**Mantenido por:** Equipo SGIR
**Contacto de seguridad:** security@sgir.com