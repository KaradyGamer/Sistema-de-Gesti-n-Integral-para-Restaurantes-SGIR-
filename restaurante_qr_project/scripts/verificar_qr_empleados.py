"""
Script para verificar tokens QR de empleados
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from app.usuarios.models import Usuario

print("=" * 60)
print("VERIFICACION DE TOKENS QR - EMPLEADOS")
print("=" * 60)
print()

empleados = Usuario.objects.filter(rol__in=['mesero', 'cocinero'], activo=True)

for emp in empleados:
    token = emp.get_qr_token()
    url = f"http://10.165.187.107:8000/usuarios/auth-qr/{token}/"

    print(f"Usuario: {emp.username}")
    print(f"Rol: {emp.get_rol_display()}")
    print(f"Token: {token}")
    print(f"URL: {url}")
    print(f"Activo: {emp.activo}")
    print("-" * 60)
