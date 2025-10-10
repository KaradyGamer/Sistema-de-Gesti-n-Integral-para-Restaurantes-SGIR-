"""
Middleware para validar que la jornada laboral esté activa
Los empleados (meseros y cocineros) no pueden interactuar si la jornada está inactiva
"""
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse


class JornadaLaboralMiddleware:
    """
    Middleware que verifica si la jornada laboral está activa
    Solo aplica para meseros y cocineros
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # URLs que NO requieren jornada activa (siempre permitidas)
        rutas_permitidas = [
            '/login/',
            '/usuarios/login-pin/',
            '/usuarios/login-admin/',
            '/usuarios/auth-qr/',
            '/usuarios/logout/',
            '/admin/',
            '/static/',
            '/media/',
        ]

        # Si la ruta está en las permitidas, continuar
        if any(request.path.startswith(ruta) for ruta in rutas_permitidas):
            response = self.get_response(request)
            return response

        # Si el usuario no está autenticado, continuar
        if not request.user.is_authenticated:
            response = self.get_response(request)
            return response

        # ✅ MEJORADO: Verificar que el usuario tenga atributo 'rol'
        try:
            user_rol = getattr(request.user, 'rol', None)
        except AttributeError:
            # Usuario sin rol (superuser de Django sin perfil)
            response = self.get_response(request)
            return response

        # Si no tiene rol definido, permitir acceso
        if not user_rol:
            response = self.get_response(request)
            return response

        # Si es admin, gerente o cajero, continuar (no necesitan jornada activa)
        if user_rol in ['admin', 'gerente', 'cajero']:
            response = self.get_response(request)
            return response

        # SOLO para meseros y cocineros: verificar jornada activa
        if user_rol in ['mesero', 'cocinero']:
            from .models import JornadaLaboral
            from django.core.cache import cache

            # ✅ OPTIMIZACIÓN: Usar caché para reducir consultas a BD
            cache_key = 'jornada_activa'
            jornada_activa = cache.get(cache_key)

            if jornada_activa is None:
                # No está en caché, consultar BD
                jornada_activa = JornadaLaboral.hay_jornada_activa()
                # Cachear por 60 segundos
                cache.set(cache_key, jornada_activa, 60)

            # Verificar si hay jornada activa
            if not jornada_activa:
                from django.contrib.auth import logout

                # ✅ MEJORADO: Mostrar mensaje más amigable
                messages.warning(
                    request,
                    '⏰ La jornada laboral ha finalizado. Tu sesión se ha cerrado automáticamente.'
                )

                # Cerrar sesión del empleado
                logout(request)

                # Redirigir al login
                return redirect('/login/')

        # Si todo está bien, continuar
        response = self.get_response(request)
        return response
