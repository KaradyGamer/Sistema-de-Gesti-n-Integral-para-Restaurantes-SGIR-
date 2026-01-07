# ═══════════════════════════════════════════
# RONDA 4: Utilidades para Reportes
# ═══════════════════════════════════════════

from datetime import datetime, timedelta
from rest_framework.response import Response


def parse_rango_fechas(request):
    """
    Extrae rango de fechas desde request.query_params.

    Retorna:
        tuple: (fecha_inicio, fecha_fin) como objetos datetime

    Si no se envía rango, retorna último mes.
    """
    desde_str = request.query_params.get('desde')
    hasta_str = request.query_params.get('hasta')

    if desde_str and hasta_str:
        try:
            fecha_inicio = datetime.strptime(desde_str, '%Y-%m-%d')
            fecha_fin = datetime.strptime(hasta_str, '%Y-%m-%d')
        except ValueError:
            return None, None
    else:
        # Por defecto: último mes
        fecha_fin = datetime.now()
        fecha_inicio = fecha_fin - timedelta(days=30)

    return fecha_inicio, fecha_fin


def require_admin_or_manager(user):
    """
    Valida que el usuario sea admin o manager.

    Retorna:
        Response o None: Si no tiene permiso retorna Response con error 403,
                         si tiene permiso retorna None
    """
    # Opciones válidas:
    # 1. Superusuario
    # 2. Usuario con rol 'admin' o 'gerente'

    if user.is_superuser:
        return None

    # Verificar rol si existe campo 'rol' en modelo Usuario
    if hasattr(user, 'rol'):
        if user.rol in ['admin', 'gerente']:
            return None

    # Si no cumple ninguna condición, denegar acceso
    return Response(
        {'error': 'Acceso denegado. Solo administradores y gerentes.'},
        status=403
    )


# ═══════════════════════════════════════════
# RONDA 4.1: Query Params Helpers
# ═══════════════════════════════════════════

def qp_bool(request, key: str, default: bool = False) -> bool:
    """
    Extrae parámetro booleano desde query params.

    Args:
        request: Request object
        key: Nombre del parámetro
        default: Valor por defecto si no existe

    Returns:
        bool: True si el valor es "1", "true", "yes", etc.
    """
    val = request.query_params.get(key)
    if val is None:
        return default
    return str(val).strip().lower() in ("1", "true", "t", "yes", "y", "si", "sí")


def qp_int(request, key: str, default: int, min_v: int = 1, max_v: int = 100) -> int:
    """
    Extrae parámetro entero desde query params con validación de rango.

    Args:
        request: Request object
        key: Nombre del parámetro
        default: Valor por defecto
        min_v: Valor mínimo permitido
        max_v: Valor máximo permitido

    Returns:
        int: Valor dentro del rango [min_v, max_v]
    """
    val = request.query_params.get(key)
    if val is None:
        return default
    try:
        n = int(val)
    except ValueError:
        return default
    if n < min_v:
        return min_v
    if n > max_v:
        return max_v
    return n


def qp_choice(request, key: str, choices: set, default=None):
    """
    Extrae parámetro desde query params validando contra opciones permitidas.

    Args:
        request: Request object
        key: Nombre del parámetro
        choices: Set de valores permitidos
        default: Valor por defecto si no existe o es inválido

    Returns:
        str o None: Valor si está en choices, default en caso contrario
    """
    val = request.query_params.get(key)
    if val is None:
        return default
    val = str(val).strip().lower()
    return val if val in choices else default