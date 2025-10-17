from django.urls import path
from .views import (
    RegistroUsuarioView,
    CustomTokenObtainPairView,
    session_login,
    session_logout,
    login_pin,
    login_admin,
    auth_qr,
    ver_todos_qr,
    ver_qr_simple
)
from .views_empleado import panel_empleado

app_name = 'usuarios'

urlpatterns = [
    # 👥 Registro de usuarios
    path('registro/', RegistroUsuarioView.as_view(), name='registro_usuario'),

    # 🔐 Login JWT (para API, mantener por compatibilidad)
    path('login/', CustomTokenObtainPairView.as_view(), name='api_login'),

    # ✅ Login con sesión Django (antiguo, mantener por compatibilidad)
    path('session-login/', session_login, name='session_login'),

    # 🆕 NUEVO SISTEMA DE LOGIN
    path('login-pin/', login_pin, name='login_pin'),  # Login con PIN
    path('login-admin/', login_admin, name='login_admin'),  # Login tradicional
    path('auth-qr/<uuid:token>/', auth_qr, name='auth_qr'),  # Autenticación por QR

    # ✅ Logout
    path('logout/', session_logout, name='session_logout'),

    # 📱 Ver todos los QR
    path('ver-qr/', ver_todos_qr, name='ver_qr'),
    path('qr/', ver_qr_simple, name='qr_simple'),  # Vista simplificada
]