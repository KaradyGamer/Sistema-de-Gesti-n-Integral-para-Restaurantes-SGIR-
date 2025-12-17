# -*- coding: utf-8 -*-
"""
Healthcheck endpoint para monitoreo del sistema
"""
from django.http import JsonResponse
from django.db import connection
from django.conf import settings
import time


def healthcheck(request):
    """
    Endpoint de healthcheck para verificar el estado del sistema.

    Verifica:
    - Conexi�n a la base de datos
    - Estado general del servidor

    Returns:
        JSON con el estado del sistema
    """
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "debug": settings.DEBUG,
        "checks": {}
    }

    # Check 1: Base de datos
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status["checks"]["database"] = "ok"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = f"error: {str(e)}"

    # Check 2: Cache (opcional)
    try:
        from django.core.cache import cache
        cache.set('healthcheck', 'ok', 10)
        if cache.get('healthcheck') == 'ok':
            health_status["checks"]["cache"] = "ok"
        else:
            health_status["checks"]["cache"] = "error"
    except Exception as e:
        health_status["checks"]["cache"] = f"error: {str(e)}"

    # Determinar c�digo HTTP seg�n estado
    status_code = 200 if health_status["status"] == "healthy" else 503

    return JsonResponse(health_status, status=status_code)
