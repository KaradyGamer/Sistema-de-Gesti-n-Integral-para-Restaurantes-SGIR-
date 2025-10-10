#!/usr/bin/env python
"""
Script para crear un usuario cajero de prueba
Ejecutar: python crear_cajero.py
"""
import os
import django

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