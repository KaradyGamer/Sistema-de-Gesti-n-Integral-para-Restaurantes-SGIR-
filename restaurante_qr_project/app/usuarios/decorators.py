"""
Decoradores personalizados para validación de roles y permisos
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse


def rol_requerido(*roles_permitidos):
    """
    Decorador que valida que el usuario tenga uno de los roles permitidos

    Uso:
        @rol_requerido('cajero', 'admin', 'gerente')
        def mi_vista(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Verificar autenticación
            if not request.user.is_authenticated:
                messages.error(request, 'Debes iniciar sesión para acceder.')
                return redirect('/login/')

            # Verificar que el usuario tenga el atributo 'rol'
            user_rol = getattr(request.user, 'rol', None)

            # Si es superusuario sin rol, permitir acceso
            if request.user.is_superuser and not user_rol:
                return view_func(request, *args, **kwargs)

            # Verificar que tenga rol
            if not user_rol:
                messages.error(request, 'Tu usuario no tiene un rol asignado.')
                return redirect('/login/')

            # Verificar que el rol esté permitido
            if user_rol not in roles_permitidos:
                messages.error(request, 'No tienes permisos para acceder a esta página.')
                return redirect('/login/')

            # Si todo está bien, ejecutar la vista
            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator


def rol_requerido_api(*roles_permitidos):
    """
    Decorador para APIs que valida roles y retorna JSON

    Uso:
        @rol_requerido_api('cajero', 'admin')
        def mi_api(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Verificar autenticación
            if not request.user.is_authenticated:
                return JsonResponse({
                    'success': False,
                    'error': 'No autenticado'
                }, status=401)

            # Verificar que el usuario tenga el atributo 'rol'
            user_rol = getattr(request.user, 'rol', None)

            # Si es superusuario sin rol, permitir acceso
            if request.user.is_superuser and not user_rol:
                return view_func(request, *args, **kwargs)

            # Verificar que tenga rol
            if not user_rol:
                return JsonResponse({
                    'success': False,
                    'error': 'Usuario sin rol asignado'
                }, status=403)

            # Verificar que el rol esté permitido
            if user_rol not in roles_permitidos:
                return JsonResponse({
                    'success': False,
                    'error': 'Permisos insuficientes'
                }, status=403)

            # Si todo está bien, ejecutar la vista
            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator


def solo_cajero(view_func):
    """
    Decorador específico para vistas exclusivas del cajero
    """
    return rol_requerido('cajero', 'admin', 'gerente')(view_func)


def solo_mesero(view_func):
    """
    Decorador específico para vistas del mesero
    """
    return rol_requerido('mesero', 'admin', 'gerente')(view_func)


def solo_cocinero(view_func):
    """
    Decorador específico para vistas del cocinero
    """
    return rol_requerido('cocinero', 'admin', 'gerente')(view_func)


def solo_admin(view_func):
    """
    Decorador específico para administradores
    """
    return rol_requerido('admin', 'gerente')(view_func)


def admin_requerido(view_func):
    """
    Decorador para vistas de AdminUX (admin, gerente, cajero)
    NO incluye superusuarios - esos usan Django Admin
    """
    return rol_requerido('admin', 'gerente', 'cajero')(view_func)


def superusuario_requerido(view_func):
    """
    Decorador para Django Admin (solo superusuarios)
    Este es el nivel más alto de acceso
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Debes iniciar sesión para acceder.')
            return redirect('/login/')

        if not request.user.is_superuser:
            messages.error(request, 'Solo superusuarios pueden acceder al Admin de Django.')
            return redirect('/adminux/')

        return view_func(request, *args, **kwargs)

    return wrapper


# ========================================
# ✅ NUEVO: RATE LIMITING
# ========================================
import logging
from django.core.cache import cache

logger = logging.getLogger('app.usuarios')


def rate_limit_login(max_attempts=5, lockout_duration=300, login_type='general'):
    """
    Decorador para rate limiting de intentos de login

    Args:
        max_attempts: Intentos permitidos antes de bloqueo (default: 5)
        lockout_duration: Tiempo de bloqueo en segundos (default: 300 = 5 min)
        login_type: Tipo de login ('qr', 'pin', 'general')

    Uso:
        @rate_limit_login(max_attempts=5, lockout_duration=300, login_type='pin')
        def mi_vista_login(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Obtener IP del cliente
            client_ip = request.META.get('HTTP_X_FORWARDED_FOR')
            if client_ip:
                client_ip = client_ip.split(',')[0].strip()
            else:
                client_ip = request.META.get('REMOTE_ADDR', 'unknown')

            # Cache keys únicos por tipo de login e IP
            attempts_key = f'{login_type}_login_attempts_{client_ip}'
            lockout_key = f'{login_type}_login_lockout_{client_ip}'

            # Verificar si está bloqueado
            if cache.get(lockout_key):
                logger.warning(
                    f"[RATE LIMIT] Login {login_type} bloqueado - IP: {client_ip}"
                )

                # ✅ Respuesta según tipo de request (verificar Content-Type y Accept)
                is_json_request = (
                    request.content_type == 'application/json' or
                    request.META.get('CONTENT_TYPE', '').startswith('application/json') or
                    request.META.get('HTTP_ACCEPT', '').startswith('application/json')
                )

                if is_json_request:
                    return JsonResponse({
                        'success': False,
                        'error': f'Demasiados intentos fallidos. Espera {lockout_duration // 60} minutos.'
                    }, status=429)
                else:
                    messages.error(
                        request,
                        f'Demasiados intentos fallidos. Espera {lockout_duration // 60} minutos.'
                    )
                    return redirect('/login/')

            # Ejecutar vista original
            response = view_func(request, *args, **kwargs)

            # Detectar si el login falló
            login_failed = False

            if isinstance(response, JsonResponse):
                # Para respuestas JSON
                try:
                    import json
                    content = json.loads(response.content.decode('utf-8'))
                    login_failed = not content.get('success', True)
                except:
                    pass
            elif hasattr(response, 'status_code') and response.status_code == 302:
                # Para redirects, verificar si va a /login/ (indica fallo)
                login_failed = '/login/' in response.url

            # Manejar intentos fallidos
            if login_failed:
                attempts = cache.get(attempts_key, 0) + 1
                cache.set(attempts_key, attempts, lockout_duration)

                if attempts >= max_attempts:
                    cache.set(lockout_key, True, lockout_duration)
                    logger.error(
                        f"[RATE LIMIT] {login_type.upper()} bloqueado tras "
                        f"{attempts} intentos - IP: {client_ip}"
                    )
                else:
                    logger.warning(
                        f"[RATE LIMIT] Intento fallido {attempts}/{max_attempts} "
                        f"para {login_type} - IP: {client_ip}"
                    )
            else:
                # Login exitoso, limpiar contadores
                cache.delete(attempts_key)
                cache.delete(lockout_key)
                logger.info(f"[RATE LIMIT] Login {login_type} exitoso - IP: {client_ip}")

            return response
        return wrapper
    return decorator
