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
            print(f"[MIDDLEWARE] Usuario NO autenticado en {request.path}")
            response = self.get_response(request)
            return response

        print(f"[MIDDLEWARE] Usuario autenticado: {request.user.username} en {request.path}")

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

            # Consultar SIEMPRE la BD (sin caché para evitar problemas)
            jornada_activa = JornadaLaboral.hay_jornada_activa()
            print(f"[MIDDLEWARE] Jornada activa: {jornada_activa} para usuario {request.user.username}")

            # Verificar si hay jornada activa
            if not jornada_activa:
                from django.contrib.auth import logout

                # ✅ MEJORADO: Mostrar mensaje más amigable
                print(f"[MIDDLEWARE] NO hay jornada activa - Cerrando sesion de {request.user.username}")
                messages.warning(
                    request,
                    'La jornada laboral ha finalizado. Tu sesion se ha cerrado automaticamente.'
                )

                # Cerrar sesión del empleado
                logout(request)

                # Redirigir al login
                return redirect('/login/')
            else:
                print(f"[MIDDLEWARE] Jornada activa OK - Permitiendo acceso a {request.path}")

        # Si todo está bien, continuar
        response = self.get_response(request)
        return response
