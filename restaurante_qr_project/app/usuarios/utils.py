from django.http import HttpResponseForbidden

def rol_requerido(rol_permitido):
    def decorador(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseForbidden("No estás autenticado.")
            if request.user.rol.lower() != rol_permitido.lower():
                return HttpResponseForbidden("No tienes permiso para acceder a esta vista.")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorador
