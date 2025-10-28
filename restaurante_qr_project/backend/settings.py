from pathlib import Path
import os
from datetime import timedelta
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)

# ✅ CORREGIDO: Permitir acceso desde cualquier IP en modo desarrollo (para QR móviles)
if DEBUG:
    ALLOWED_HOSTS = ['*']  # Permitir todas las IPs en desarrollo
else:
    ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')  # Solo acceso local en producción

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

    # Apps del proyecto
    'app.usuarios',
    'app.mesas',
    'app.productos',
    'app.pedidos',
    'app.caja',  # Módulo de caja
    'app.adminux',  # Panel de administración moderno

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
            BASE_DIR / 'templates' / 'html',  # Archivos HTML dentro de templates/html/
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

# 🗃️ Base de datos
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
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

# ✅ Permitir todos los orígenes en desarrollo (para escaneo QR desde celular)
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True

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
LOGIN_URL = '/login/'  # ✅ Tu página de login personalizada
LOGIN_REDIRECT_URL = '/'  # ✅ Redirigir al home después del login
LOGOUT_REDIRECT_URL = '/login/'  # ✅ Redirigir al login después del logout

# 🛡️ Prevenir redirección automática al admin
ADMIN_URL = '/admin/'  # ✅ Mantener admin en su propia ruta

# 🔧 Configuración de sesiones
SESSION_COOKIE_AGE = 86400  # 24 horas
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# 🛡️ Seguridad de cookies (desde variables de entorno)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=False, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=False, cast=bool)
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

# 🔐 CONFIGURACIONES DE SEGURIDAD PARA PRODUCCIÓN
# Descomenta estas líneas cuando DEBUG=False (producción)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000  # 1 año
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
