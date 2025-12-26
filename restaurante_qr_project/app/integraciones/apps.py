from django.apps import AppConfig


class IntegracionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.integraciones'
    verbose_name = 'Integraciones Externas (n8n, webhooks)'
