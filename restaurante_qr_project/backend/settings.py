from pathlib import Path
import os
from datetime import timedelta
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')  # Solo acceso local

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=8),  # ✅ Token dura 8 horas
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),  # ✅ Refresh token dura 7 días
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
            BASE_DIR.parent / 'templates',  # Templates en la raíz del proyecto
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
    os.path.join(BASE_DIR.parent, 'staticfiles'),  # ✅ Archivos estáticos en la raíz del proyecto
]

STATIC_ROOT = os.path.join(BASE_DIR, 'static_collected')  # ✅ Carpeta donde collectstatic recopila archivos

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# 🧠 Django por defecto usa BigAutoField
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 👤 Usuario personalizado
AUTH_USER_MODEL = 'usuarios.Usuario'

# 🌐 CORS
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='http://localhost:3000,http://127.0.0.1:3000').split(',')

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

# 🔧 Configuración de sesiones (soluciona problemas de cookies)
SESSION_COOKIE_AGE = 86400  # 24 horas
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# 🛡️ Configuración de seguridad para desarrollo (descomenta si hay problemas)
# SESSION_COOKIE_SECURE = False  # Solo para desarrollo local
# CSRF_COOKIE_SECURE = False     # Solo para desarrollo local

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