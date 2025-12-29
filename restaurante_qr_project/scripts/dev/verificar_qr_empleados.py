"""
Script para verificar tokens QR de empleados
Uso: python scripts/verificar_qr_empleados.py [IP:PUERTO]
Ejemplo: python scripts/verificar_qr_empleados.py localhost:8000
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

# Leer IP de argumento o usar valor por defecto
if len(sys.argv) > 1:
    ip_servidor = sys.argv[1].strip()
else:
    ip_servidor = "localhost:8000"
    print(f"Usando IP por defecto: {ip_servidor}")
    print(f"Para especificar otra: python scripts/verificar_qr_empleados.py <IP:PUERTO>")

print("=" * 60)
print("VERIFICACION DE TOKENS QR - EMPLEADOS")
print("=" * 60)
print(f"Servidor: {ip_servidor}")
print()

empleados = Usuario.objects.filter(rol__in=['mesero', 'cocinero'], activo=True)

if empleados.count() == 0:
    print("No se encontraron empleados (mesero/cocinero) activos")
else:
    for emp in empleados:
        token = emp.get_qr_token()
        url = f"http://{ip_servidor}/usuarios/auth-qr/{token}/"

        print(f"Usuario: {emp.username}")
        print(f"Rol: {emp.get_rol_display()}")
        print(f"Token: {token}")
        print(f"URL: {url}")
        print(f"Activo: {emp.activo}")
        print("-" * 60)
