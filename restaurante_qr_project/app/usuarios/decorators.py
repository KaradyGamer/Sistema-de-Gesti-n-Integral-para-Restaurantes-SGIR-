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
                messages.error(request, f'No tienes permisos para acceder a esta página.')
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
