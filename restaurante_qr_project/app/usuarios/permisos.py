from rest_framework.permissions import BasePermission

# Clase base para permisos que verifica el rol del usuario
class EsRol(BasePermission):
    rol = None  # Debe ser definido en las subclases

    def has_permission(self, request, view):
        # Verifica que el usuario esté autenticado y que su rol coincida
        return bool(request.user and request.user.is_authenticated and request.user.rol == self.rol)

# Permiso para cocinero
class EsCocinero(EsRol):
    rol = 'cocinero'

# Permiso para mesero
class EsMesero(EsRol):
    rol = 'mesero'

# Permiso para cajero
class EsCajero(EsRol):
    rol = 'cajero'

# Permiso para gerente
class EsGerente(EsRol):
    rol = 'gerente'

# Permiso para administrador
class EsAdministrador(EsRol):
    rol = 'admin'
