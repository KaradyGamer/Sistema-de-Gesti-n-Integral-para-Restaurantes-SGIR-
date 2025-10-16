#!/usr/bin/env python
"""
Script para crear un usuario cajero de prueba
Ejecutar desde raíz del proyecto: python scripts/crear_cajero.py
"""
import os
import sys
import django

# Agregar el directorio padre al path para importar módulos de Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar encoding para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from app.usuarios.models import Usuario

def crear_cajero():
    """Crea un usuario cajero de prueba"""

    # Verificar si ya existe
    if Usuario.objects.filter(username='cajero1').exists():
        print("⚠️  El usuario 'cajero1' ya existe.")
        cajero = Usuario.objects.get(username='cajero1')
        print(f"   Usuario: {cajero.username}")
        print(f"   Rol: {cajero.rol}")
        print(f"   Nombre: {cajero.first_name} {cajero.last_name}")
        return

    # Crear nuevo usuario
    try:
        cajero = Usuario.objects.create_user(
            username='cajero1',
            password='cajero123',
            first_name='Juan',
            last_name='Pérez',
            email='cajero1@restaurante.com',
            rol='cajero'
        )

        print("✅ Usuario cajero creado exitosamente!")
        print(f"   Usuario: {cajero.username}")
        print(f"   Contraseña: cajero123")
        print(f"   Rol: {cajero.rol}")
        print(f"   Nombre: {cajero.first_name} {cajero.last_name}")
        print("\n🚀 Ahora puedes iniciar sesión en:")
        print("   http://127.0.0.1:8000/login/")
        print("   Selecciona rol: 💰 Cajero")

    except Exception as e:
        print(f"❌ Error al crear usuario: {str(e)}")

if __name__ == '__main__':
    print("=" * 50)
    print("🏪 CREAR USUARIO CAJERO")
    print("=" * 50)
    crear_cajero()
    print("=" * 50)