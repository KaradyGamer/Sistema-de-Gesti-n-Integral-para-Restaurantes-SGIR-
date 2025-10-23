"""
Script para crear usuarios administradores con credenciales específicas
- Django Admin: admin / admin123
- AdminUX: admin / admin1234
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from app.usuarios.models import Usuario
from django.contrib.auth.hashers import make_password


def crear_admins():
    """Crea los usuarios administradores con credenciales específicas"""

    print("=" * 60)
    print("CREACIÓN DE USUARIOS ADMINISTRADORES")
    print("=" * 60)

    # Usuario para Django Admin
    username_django = 'admin'
    password_django = 'admin123'

    # Usuario para AdminUX
    username_ux = 'admin'
    password_ux = 'admin1234'

    # Verificar si ya existe el usuario admin
    if Usuario.objects.filter(username=username_django).exists():
        admin_user = Usuario.objects.get(username=username_django)
        print(f"\n[OK] Usuario '{username_django}' ya existe")

        # Actualizar contraseña
        admin_user.set_password(password_django)
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.rol = 'admin'
        admin_user.first_name = 'Administrador'
        admin_user.last_name = 'Sistema'
        admin_user.activo = True
        admin_user.save()
        print(f"[OK] Contrasena actualizada para Django Admin")
    else:
        # Crear nuevo usuario admin
        admin_user = Usuario.objects.create(
            username=username_django,
            password=make_password(password_django),
            email='admin@restaurante.com',
            first_name='Administrador',
            last_name='Sistema',
            rol='admin',
            is_staff=True,
            is_superuser=True,
            activo=True
        )
        print(f"\n[OK] Usuario '{username_django}' creado exitosamente")

    print("\n" + "=" * 60)
    print("CREDENCIALES DE ACCESO")
    print("=" * 60)

    print("\n[DJANGO ADMIN] (Panel nativo)")
    print(f"   URL: http://localhost:8000/admin/")
    print(f"   Usuario: {username_django}")
    print(f"   Contrasena: {password_django}")

    print("\n[ADMINUX] (Panel personalizado)")
    print(f"   URL: http://localhost:8000/adminux/")
    print(f"   Usuario: {username_ux}")
    print(f"   Contrasena: {password_ux}")
    print(f"   Nota: Usa las mismas credenciales del usuario admin")

    print("\n" + "=" * 60)
    print("[OK] PROCESO COMPLETADO")
    print("=" * 60)
    print("\nPuedes acceder a ambos paneles con el usuario 'admin'")
    print("y las contrasenas especificadas arriba.\n")


if __name__ == '__main__':
    try:
        crear_admins()
    except Exception as e:
        print(f"\n[ERROR] Error al crear administradores: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
