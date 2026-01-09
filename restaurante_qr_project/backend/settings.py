"""
Configuración de Django para el proyecto SGIR (Sistema de Gestión Integral para Restaurantes).

IMPORTANTE - Encoding en Windows:
- Este proyecto usa PostgreSQL con encoding UTF-8
- En Windows con locale es_ES (cp1252), puede haber conflictos de encoding
- SOLUCIÓN: Ejecutar Django através de Docker para garantizar UTF-8 consistente
- Ver README.md para instrucciones de uso con Docker

IMPORTANTE - Variables de entorno:
- Todas las configuraciones sensibles se leen desde .env (python-decouple)
- NUNCA commitear .env al repositorio
- Usar config() en lugar de os.getenv() para leer variables

IMPORTANTE - Base de datos:
- PostgreSQL EXCLUSIVO (sin fallback a SQLite)
- Requiere container Docker o instalación local de PostgreSQL
"""
from pathlib import Path
import os
from datetime import timedelta
from decouple import config
import sys

BASE_DIR = Path(__file__).resolve().parent.parent

# ✅ SEGURIDAD CRÍTICA: Validar SECRET_KEY obligatoria
try:
    SECRET_KEY = config('SECRET_KEY')
except Exception:
    print("ERROR CRÍTICO: SECRET_KEY no configurada en .env", file=sys.stderr)
    print("Genera una nueva con: python -c \"from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())\"", file=sys.stderr)
    sys.exit(1)

DEBUG = config('DEBUG', default=False, cast=bool)

# Validar que SECRET_KEY no sea la de ejemplo/desarrollo
if 'django-insecure' in SECRET_KEY or 'CAMBIAR_ESTO' in SECRET_KEY:
    if not DEBUG:
        print("ERROR CRÍTICO: SECRET_KEY de desarrollo detectada en producción", file=sys.stderr)
        sys.exit(1)
    else:
        print("ADVERTENCIA: Usando SECRET_KEY de desarrollo. Cambiar antes de producción.", file=sys.stderr)

# ✅ SEGURIDAD: Leer ALLOWED_HOSTS desde .env siempre
# En desarrollo puedes agregar '*' al .env si necesitas acceso desde cualquier IP
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

# ⚠️ Validación de seguridad: si DEBUG=False y ALLOWED_HOSTS vacío, Django lanzará error
if not DEBUG and not ALLOWED_HOSTS:
    raise ValueError('ALLOWED_HOSTS debe estar configurado cuando DEBUG=False')

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=config('JWT_ACCESS_TOKEN_LIFETIME', default=60, cast=int)),  # ✅ 60 minutos por defecto
    'REFRESH_TOKEN_LIFETIME': timedelta(days=config('JWT_REFRESH_TOKEN_LIFETIME', default=14, cast=int)),  # ✅ 14 días por defecto
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
}

# 📦 Aplicaciones instaladas
INSTALLED_APPS = [
    "admin_interface",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # ✅ Agregado para QR codes

    # Apps externas
    'rest_framework',
    'django_filters',
    'corsheaders',
    'django_extensions',  # Management commands (show_urls, etc.)

    # Apps del proyecto
    'app.usuarios',
    'app.mesas',
    'app.productos',
    'app.pedidos',
    'app.caja',  # Módulo de caja
    'app.adminux',  # Panel de administración moderno
    'app.inventario',  # Gestión de insumos
    'app.configuracion',  # Configuración del sistema

    #reportes contables
    'app.reportes',
    'app.reservas',

    "colorfield",
]

# Site ID para django.contrib.sites
SITE_ID = 1

X_FRAME_OPTIONS = "SAMEORIGIN"

# 🌐 Middleware
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ✅ WhiteNoise para archivos estáticos
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # ✅ Soporte de idiomas para admin_interface
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'app.caja.middleware.JornadaLaboralMiddleware',  # ✅ Validar jornada laboral activa
]

ROOT_URLCONF = 'backend.urls'

# 📁 Templates (HTML)
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',           # Busca en templates/ (para base.html)
            BASE_DIR / 'templates' / 'html',  # Busca en templates/html/ (para otros templates)
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'

# 🗃️ Base de datos - PostgreSQL ÚNICO (sin fallback a SQLite)
# ⚠️ CRÍTICO: Este proyecto usa PostgreSQL exclusivamente
# NO hay soporte para SQLite - todas las operaciones requieren PostgreSQL
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("POSTGRES_DB"),
        "USER": config("POSTGRES_USER"),
        "PASSWORD": config("POSTGRES_PASSWORD"),
        "HOST": config("POSTGRES_HOST", default="db"),
        "PORT": config("POSTGRES_PORT", default="5432"),
        "OPTIONS": {
            "client_encoding": "UTF8",
        },
    }
}

# 🔐 Validaciones de contraseña
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# 🌍 Internacionalización
LANGUAGE_CODE = 'es-bo'  # ✅ SOLUCIONADO: Cambiar a Bolivia
TIME_ZONE = 'America/La_Paz'  # ✅ SOLUCIONADO: Zona horaria de Bolivia
USE_I18N = True
USE_L10N = True
USE_TZ = True

# ✅ SOLUCIONADO: Configuración de moneda boliviana
USE_THOUSAND_SEPARATOR = True
THOUSAND_SEPARATOR = '.'
DECIMAL_SEPARATOR = ','

# 🖼️ Archivos estáticos y multimedia
STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'templates'),  # Templates contiene css/, js/, etc.
    os.path.join(BASE_DIR, 'static'),  # ✅ Carpeta static/ para PWA y otros
]

STATIC_ROOT = os.path.join(BASE_DIR, 'static_collected')  # ✅ Carpeta donde collectstatic recopila archivos

# ✅ WhiteNoise - Compresión y caché de archivos estáticos
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# 🧠 Django por defecto usa BigAutoField
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 👤 Usuario personalizado
AUTH_USER_MODEL = 'usuarios.Usuario'

# 🌐 CORS
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='http://localhost:3000,http://127.0.0.1:3000').split(',')

# ✅ CSRF - Orígenes confiables desde variable de entorno
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='http://localhost:8000,http://127.0.0.1:8000'
).split(',')

# 🔒 SEGURIDAD: NUNCA usar CORS_ALLOW_ALL_ORIGINS (ni en desarrollo)
# Para desarrollo con celular, agregar IPs explícitas a CORS_ALLOWED_ORIGINS en .env
# Ejemplo: CORS_ALLOWED_ORIGINS=http://192.168.1.100:8000,http://10.0.0.5:8000

# 🔐 Configuración de DRF y JWT
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # ✅ Soporte para sesión Django
    ],
}

# ✅ CONFIGURACIÓN DE AUTENTICACIÓN COMPLETA
# LOGIN_URL se mantiene en /admin/login/ para el admin nativo
# AdminUX usa /staff/login/ en sus decorators
LOGIN_URL = '/admin/login/'  # ✅ Login por defecto (admin nativo)
LOGIN_REDIRECT_URL = '/adminux/'  # ✅ Redirección después del login (panel UX)
LOGOUT_REDIRECT_URL = '/staff/login/'  # ✅ Redirección después del logout (login del personal)

# 🛡️ Prevenir redirección automática al admin
ADMIN_URL = '/admin/'  # ✅ Mantener admin en su propia ruta

# 🔧 Configuración de sesiones
SESSION_COOKIE_AGE = 86400  # 24 horas

# 🔒 SEGURIDAD: False para evitar sobrecarga de BD
# Django solo guardará la sesión si hay cambios (no en cada request)
# Esto reduce writes innecesarios y mejora performance
SESSION_SAVE_EVERY_REQUEST = False

SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# 🔒 CONFIGURACIÓN DE SEGURIDAD CONSOLIDADA
# ✅ HOTFIX-1: Cookies simplificadas basadas en DEBUG

if not DEBUG:
    # HTTPS/SSL
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
    SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)  # 1 año
    SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True, cast=bool)
    SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=True, cast=bool)

    # Content Security
    X_FRAME_OPTIONS = 'DENY'
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True

    # Proxy
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Cookies (única definición, basada en DEBUG)
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = config('SESSION_COOKIE_HTTPONLY', default=True, cast=bool)
CSRF_COOKIE_HTTPONLY = config('CSRF_COOKIE_HTTPONLY', default=True, cast=bool)
SESSION_COOKIE_SAMESITE = config('SESSION_COOKIE_SAMESITE', default='Lax')
CSRF_COOKIE_SAMESITE = config('CSRF_COOKIE_SAMESITE', default='Lax')

# 🚫 Prevenir redirecciones no deseadas
APPEND_SLASH = True
PREPEND_WWW = False

# ⚡ CONFIGURACIÓN DE CACHÉ (para optimizar middleware)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': 300,  # 5 minutos por defecto
        'OPTIONS': {
            'MAX_ENTRIES': 1000
        }
    }
}
# 📊 CONFIGURACIÓN DE LOGGING
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module} {process:d} {thread:d} - {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'when': 'midnight',
            'interval': 1,
            'backupCount': 7,
            'formatter': 'verbose',
            'delay': True,
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'errors.log'),
            'when': 'midnight',
            'interval': 1,
            'backupCount': 7,
            'formatter': 'verbose',
            'delay': True,
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'app': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Crear directorio de logs si no existe
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# ✅ PATCH-001: Bloque duplicado ELIMINADO
# Configuración de seguridad consolidada en líneas 216-242
