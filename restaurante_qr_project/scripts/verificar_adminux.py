#!/usr/bin/env python
"""
Script de Verificacion del Panel AdminUX
SGIR v38.8

Verifica que:
1. Las rutas esten correctamente configuradas
2. Los modelos tengan los campos correctos
3. La autenticacion funcione correctamente
"""

import os
import sys
import django

# Configurar Django
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

django.setup()

from django.urls import reverse, NoReverseMatch
from django.apps import apps
from django.contrib.auth import get_user_model

print("=" * 60)
print("VERIFICACION DEL PANEL ADMINUX")
print("=" * 60)

# 1. Verificar URLs
print("\n[1] Verificando URLs...")
try:
    admin_url = reverse('admin:index')
    print(f"   [OK] Admin nativo: {admin_url}")
except NoReverseMatch:
    print("   [ERROR] No se encontro la URL del admin")

try:
    adminux_url = reverse('adminux:dashboard')
    print(f"   [OK] AdminUX dashboard: {adminux_url}")
except NoReverseMatch:
    print("   [ERROR] No se encontro la URL de AdminUX")

# 2. Verificar modelos y campos
print("\n[2] Verificando modelos...")
try:
    Categoria = apps.get_model("productos", "Categoria")
    campos_categoria = [f.name for f in Categoria._meta.get_fields()]

    if 'activo' in campos_categoria:
        print(f"   [OK] Categoria.activo existe")
    elif 'activa' in campos_categoria:
        print(f"   [WARN] Categoria usa 'activa' (femenino)")
    else:
        print(f"   [ERROR] Categoria no tiene campo activo/activa")

    print(f"   [INFO] Campos: {', '.join(campos_categoria[:10])}")
except Exception as e:
    print(f"   [ERROR] Al verificar Categoria: {e}")

try:
    Producto = apps.get_model("productos", "Producto")
    campos_producto = [f.name for f in Producto._meta.get_fields()]

    if 'stock_actual' in campos_producto:
        print(f"   [OK] Producto.stock_actual existe")
    else:
        print(f"   [WARN] Producto no tiene campo stock_actual")

    if 'activo' in campos_producto:
        print(f"   [OK] Producto.activo existe")
except Exception as e:
    print(f"   [ERROR] Al verificar Producto: {e}")

# 3. Verificar usuarios staff
print("\n[3] Verificando usuarios staff...")
try:
    Usuario = get_user_model()
    staff_users = Usuario.objects.filter(is_staff=True)
    print(f"   [OK] Usuarios staff encontrados: {staff_users.count()}")

    for user in staff_users[:5]:
        print(f"      - {user.username} (activo: {user.is_active})")

    if staff_users.count() == 0:
        print("\n   [WARN] No hay usuarios staff")
        print("      Crear uno con:")
        print("      python manage.py shell")
        print("      >>> from app.usuarios.models import Usuario")
        print("      >>> user = Usuario.objects.get(username='admin')")
        print("      >>> user.is_staff = True")
        print("      >>> user.save()")
except Exception as e:
    print(f"   [ERROR] Al verificar usuarios: {e}")

# 4. Verificar funcion safe_count
print("\n[4] Verificando helper functions...")
try:
    from app.adminux.views import safe_count, safe_get_model, admin_url_for
    print("   [OK] safe_count() importada correctamente")
    print("   [OK] safe_get_model() importada correctamente")
    print("   [OK] admin_url_for() importada correctamente")
except ImportError as e:
    print(f"   [ERROR] Al importar helpers: {e}")

# 5. Verificar templates
print("\n[5] Verificando templates...")
import os
from django.conf import settings

dashboard_path = os.path.join(
    settings.BASE_DIR,
    'templates',
    'html',
    'adminux',
    'dashboard.html'
)

if os.path.exists(dashboard_path):
    print(f"   [OK] Template dashboard.html existe")
    size = os.path.getsize(dashboard_path)
    print(f"      Tamano: {size / 1024:.1f} KB")
else:
    print(f"   [ERROR] Template dashboard.html no encontrado")

base_path = os.path.join(settings.BASE_DIR, 'templates', 'base.html')
if os.path.exists(base_path):
    print(f"   [OK] Template base.html existe")
else:
    print(f"   [ERROR] Template base.html no encontrado")

# 6. Verificar Tailwind CSS
print("\n[6] Verificando Tailwind CSS...")
try:
    with open(base_path, 'r', encoding='utf-8') as f:
        content = f.read()
        if 'tailwindcss.com' in content:
            print("   [OK] Tailwind CSS CDN configurado")
        else:
            print("   [ERROR] Tailwind CSS no encontrado en base.html")
except Exception as e:
    print(f"   [WARN] No se pudo verificar Tailwind: {e}")

# Resumen final
print("\n" + "=" * 60)
print("RESUMEN DE VERIFICACION")
print("=" * 60)
print("""
Para acceder al panel AdminUX:

1. Asegurate de tener un usuario staff:
   python manage.py shell
   >>> from app.usuarios.models import Usuario
   >>> user = Usuario.objects.get(username='admin')
   >>> user.is_staff = True
   >>> user.save()

2. Inicia el servidor:
   python manage.py runserver

3. Accede a:
   http://127.0.0.1:8000/adminux/

4. Si no estas logueado, seras redirigido a:
   http://127.0.0.1:8000/admin/login/

5. Admin nativo de Django:
   http://127.0.0.1:8000/admin/
""")

print("[OK] Verificacion completada")
print("=" * 60)
