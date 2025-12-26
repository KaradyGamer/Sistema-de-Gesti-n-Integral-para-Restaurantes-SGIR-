"""
Autenticación por API KEY para integraciones externas (n8n, webhooks)
"""
from rest_framework import authentication, exceptions
from django.conf import settings
import os


class APIKeyAuthentication(authentication.BaseAuthentication):
    """
    Autenticación simple por API KEY en header X-API-KEY.

    Uso:
        curl -H "X-API-KEY: tu_clave_secreta" http://localhost:8000/api/integraciones/health/
    """

    def authenticate(self, request):
        api_key = request.META.get('HTTP_X_API_KEY')

        if not api_key:
            return None  # No intentar autenticación (dejar que otros métodos lo intenten)

        # Obtener API_KEY configurada desde .env
        expected_key = os.getenv('N8N_API_KEY') or settings.N8N_API_KEY

        if api_key != expected_key:
            raise exceptions.AuthenticationFailed('API KEY inválida')

        # No hay usuario asociado a API KEY, devolver None como usuario
        # pero marcar request como autenticado
        return (None, None)
