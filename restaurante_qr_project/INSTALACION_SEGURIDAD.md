# Configuración de Seguridad y Responsive - SGIR v38.0

## Cambios Implementados

### 1. Archivos Creados

#### Seguridad
- `requirements.txt` - Lista completa de dependencias
- `static/pwa/manifest.json` - Configuración PWA
- `static/pwa/service-worker.js` - Funcionalidad offline
- `INSTALACION_SEGURIDAD.md` - Esta guía

#### Responsive
- `static/css/util/responsive.css` - Utilidades CSS responsive
- `static/js/responsive-tables.js` - Wrapper automático para tablas

### 2. Archivos Actualizados

#### Seguridad
- `.env` - Variables de seguridad añadidas
- `backend/settings.py` - Configuración de seguridad mejorada

#### Templates Responsive
- `templates/html/adminux/base_form.html` - {% load static %} + responsive utilities
- `templates/html/adminux/base_list.html` - {% load static %} + responsive utilities

## Instalación de Dependencias

### Paso 1: Instalar paquetes nuevos
```bash
pip install whitenoise gunicorn djangorestframework-simplejwt
```

### Paso 2: Verificar instalación completa
```bash
pip install -r requirements.txt
```

## Configuración Implementada

### JWT Tokens
- Token de acceso: **60 minutos** (configurable en `.env`)
- Token de refresco: **14 días** (configurable en `.env`)
- Rotación automática de tokens
- Blacklist después de rotación

### WhiteNoise
- Middleware activado para servir archivos estáticos en producción
- Compresión automática de archivos
- Cache de archivos estáticos
- Storage backend: `CompressedManifestStaticFilesStorage`

### CSRF y CORS
- CSRF_TRUSTED_ORIGINS ahora desde variable de entorno
- CORS_ALLOWED_ORIGINS configurable
- Cookies seguras con HttpOnly y SameSite

### PWA (Progressive Web App)
- manifest.json con metadata de la aplicación
- service-worker.js con estrategia de caché Network First
- Soporte para instalación en dispositivos móviles
- Funcionalidad offline básica

## Variables de Entorno Añadidas

En `.env` se agregaron:

```env
# JWT
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=14

# CSRF
CSRF_TRUSTED_ORIGINS=http://localhost:8000,...

# Cookies (Producción)
# SESSION_COOKIE_SECURE=True
# CSRF_COOKIE_SECURE=True
# SESSION_COOKIE_HTTPONLY=True
# CSRF_COOKIE_HTTPONLY=True
# SESSION_COOKIE_SAMESITE=Strict
# CSRF_COOKIE_SAMESITE=Strict
```

## Preparación para Producción

### 1. Recopilar archivos estáticos
```bash
python manage.py collectstatic --noinput
```

### 2. Actualizar .env para producción
Descomentar en `.env`:
```env
DEBUG=False
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
CSRF_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Strict
CSRF_COOKIE_SAMESITE=Strict
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

### 3. Ejecutar con Gunicorn
```bash
gunicorn backend.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

## Notas Importantes

1. **WhiteNoise**: Los archivos estáticos se sirven automáticamente sin necesidad de nginx
2. **PWA**: Necesitas crear íconos en `static/pwa/icon-192x192.png` y `icon-512x512.png`
3. **HTTPS**: Las cookies seguras solo funcionan con HTTPS en producción
4. **Service Worker**: Se activa automáticamente al visitar la aplicación

## Verificación

### Comprobar que settings.py carga correctamente
```bash
python manage.py check
```

### Ver configuración actual
```bash
python manage.py diffsettings
```

### Probar recolección de estáticos
```bash
python manage.py collectstatic --dry-run
```

## Próximos Pasos Opcionales

1. Crear íconos PWA (192x192px y 512x512px)
2. Configurar servidor web (nginx/Apache) como proxy inverso
3. Implementar SSL/TLS con Let's Encrypt
4. Configurar base de datos PostgreSQL para producción
5. Implementar sistema de backup automático

## Mejoras Responsive

### Archivos Creados
1. **static/css/util/responsive.css** - Utilidades CSS:
   - `.table-responsive` - Contenedor con scroll horizontal
   - `.img-fluid` - Imágenes adaptables
   - `.container-fluid` - Prevención de overflow
   - Media queries para móvil (≤576px), tablet (≤768px), desktop (≥992px)
   - Clases de utilidad (.hide-sm, .show-sm, .stack-sm, etc.)

2. **static/js/responsive-tables.js** - Funcionalidad JavaScript:
   - Envuelve tablas automáticamente en `.table-responsive`
   - Añade indicador visual de scroll
   - Observa cambios del DOM para tablas dinámicas
   - Detecta orientación del dispositivo

### Templates Actualizados
- **base_form.html** y **base_list.html**:
  - Añadido `{% load static %}` al inicio
  - Cambiado rutas absolutas a `{% static 'path' %}`
  - Incluidos archivos responsive.css y responsive-tables.js
  - Meta viewport ya existente (✓)

### Análisis de Templates
- **37 templates HTML** analizados
- **Todos** tienen `{% load static %}` donde es necesario
- **Todos** los HTMLs completos tienen meta viewport
- **0 problemas** críticos encontrados

### Resultado
- Tablas con scroll horizontal automático en móvil
- Imágenes adaptables
- Sin overflow horizontal en ninguna pantalla
- Layout responsive en móvil/tablet/desktop

## Collectstatic
```bash
python manage.py collectstatic --noinput
# Resultado: 308 static files copied to 'static_collected'
```

## Versión
**SGIR v38.0 - Configuración de Seguridad y Responsive**
Fecha: 2025-10-27
