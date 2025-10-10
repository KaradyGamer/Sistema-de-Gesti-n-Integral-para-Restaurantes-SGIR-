"""
Script para crear datos iniciales del restaurante
Ejecutar con: python crear_datos_iniciales.py
"""
import os
import sys
import django

# Configurar encoding para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from app.usuarios.models import Usuario
from app.productos.models import Producto, Categoria
from app.mesas.models import Mesa
from decimal import Decimal

def crear_usuarios():
    print("\n" + "="*50)
    print("CREANDO USUARIOS")
    print("="*50)

    # Admin
    admin, created = Usuario.objects.get_or_create(
        username='admin',
        defaults={
            'first_name': 'Administrador',
            'last_name': 'Sistema',
            'email': 'admin@restaurante.com',
            'rol': 'admin',
            'activo': True,
            'areas_permitidas': ['mesero', 'cocina', 'caja', 'reportes'],
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        admin.set_password('admin123')
        admin.save()
        print(f"✅ Admin creado: username='admin', password='admin123'")
    else:
        # Actualizar permisos si ya existe
        admin.is_staff = True
        admin.is_superuser = True
        admin.activo = True
        admin.areas_permitidas = ['mesero', 'cocina', 'caja', 'reportes']
        admin.save()
        print(f"✅ Admin actualizado: username='admin' (permisos de superusuario)")

    # Cajero 1
    cajero1, created = Usuario.objects.get_or_create(
        username='cajero1',
        defaults={
            'first_name': 'María',
            'last_name': 'González',
            'email': 'cajero1@restaurante.com',
            'rol': 'cajero',
            'pin': '1000',
            'activo': True,
            'areas_permitidas': ['caja']
        }
    )
    if created:
        cajero1.set_password('cajero123')
        cajero1.save()
        print(f"✅ Cajero1 creado: username='cajero1', PIN='1000'")
    else:
        print(f"ℹ️  Cajero1 ya existe: username='cajero1'")

    # Cajero 2
    cajero2, created = Usuario.objects.get_or_create(
        username='cajero2',
        defaults={
            'first_name': 'Pedro',
            'last_name': 'Ramírez',
            'email': 'cajero2@restaurante.com',
            'rol': 'cajero',
            'pin': '1001',
            'activo': True,
            'areas_permitidas': ['caja']
        }
    )
    if created:
        cajero2.set_password('cajero123')
        cajero2.save()
        print(f"✅ Cajero2 creado: username='cajero2', PIN='1001'")
    else:
        print(f"ℹ️  Cajero2 ya existe: username='cajero2'")

    # Mesero 1
    mesero1, created = Usuario.objects.get_or_create(
        username='mesero1',
        defaults={
            'first_name': 'Ana',
            'last_name': 'López',
            'email': 'mesero1@restaurante.com',
            'rol': 'mesero',
            'activo': True,
            'areas_permitidas': ['mesero']
        }
    )
    if created:
        mesero1.set_password('mesero123')
        mesero1.save()
        print(f"✅ Mesero1 creado: username='mesero1' (acceso por QR)")
    else:
        print(f"ℹ️  Mesero1 ya existe: username='mesero1'")

    # Cocinero 1
    cocinero1, created = Usuario.objects.get_or_create(
        username='cocinero1',
        defaults={
            'first_name': 'Carlos',
            'last_name': 'Martínez',
            'email': 'cocinero1@restaurante.com',
            'rol': 'cocinero',
            'activo': True,
            'areas_permitidas': ['cocina']
        }
    )
    if created:
        cocinero1.set_password('cocinero123')
        cocinero1.save()
        print(f"✅ Cocinero1 creado: username='cocinero1' (acceso por QR)")
    else:
        print(f"ℹ️  Cocinero1 ya existe: username='cocinero1'")

def crear_categorias_productos():
    print("\n" + "="*50)
    print("CREANDO CATEGORÍAS Y PRODUCTOS")
    print("="*50)

    # Categorías
    cat_entradas, _ = Categoria.objects.get_or_create(nombre='Entradas')
    cat_principales, _ = Categoria.objects.get_or_create(nombre='Platos Principales')
    cat_bebidas, _ = Categoria.objects.get_or_create(nombre='Bebidas')
    cat_postres, _ = Categoria.objects.get_or_create(nombre='Postres')

    print(f"✅ Categorías creadas")

    # Productos - Entradas
    productos_entradas = [
        {'nombre': 'Empanadas de Carne', 'precio': Decimal('5.00'), 'stock': 50},
        {'nombre': 'Empanadas de Queso', 'precio': Decimal('4.50'), 'stock': 50},
        {'nombre': 'Sopa del Día', 'precio': Decimal('8.00'), 'stock': 30},
    ]

    for p in productos_entradas:
        prod, created = Producto.objects.get_or_create(
            nombre=p['nombre'],
            defaults={
                'categoria': cat_entradas,
                'precio': p['precio'],
                'disponible': True,
                'requiere_inventario': True,
                'stock_actual': p['stock'],
                'stock_minimo': 10
            }
        )
        if created:
            print(f"  ✅ {p['nombre']} - Bs/ {p['precio']}")

    # Productos - Principales
    productos_principales = [
        {'nombre': 'Pique Macho', 'precio': Decimal('35.00'), 'stock': 30},
        {'nombre': 'Silpancho', 'precio': Decimal('25.00'), 'stock': 40},
        {'nombre': 'Sajta de Pollo', 'precio': Decimal('28.00'), 'stock': 35},
        {'nombre': 'Charque', 'precio': Decimal('32.00'), 'stock': 25},
        {'nombre': 'Fricase', 'precio': Decimal('30.00'), 'stock': 30},
    ]

    for p in productos_principales:
        prod, created = Producto.objects.get_or_create(
            nombre=p['nombre'],
            defaults={
                'categoria': cat_principales,
                'precio': p['precio'],
                'disponible': True,
                'requiere_inventario': True,
                'stock_actual': p['stock'],
                'stock_minimo': 10
            }
        )
        if created:
            print(f"  ✅ {p['nombre']} - Bs/ {p['precio']}")

    # Productos - Bebidas
    productos_bebidas = [
        {'nombre': 'Refresco 500ml', 'precio': Decimal('5.00'), 'stock': 100},
        {'nombre': 'Jugo Natural', 'precio': Decimal('8.00'), 'stock': 50},
        {'nombre': 'Cerveza Nacional', 'precio': Decimal('12.00'), 'stock': 80},
        {'nombre': 'Agua Mineral', 'precio': Decimal('4.00'), 'stock': 100},
        {'nombre': 'Café', 'precio': Decimal('6.00'), 'stock': 60},
    ]

    for p in productos_bebidas:
        prod, created = Producto.objects.get_or_create(
            nombre=p['nombre'],
            defaults={
                'categoria': cat_bebidas,
                'precio': p['precio'],
                'disponible': True,
                'requiere_inventario': True,
                'stock_actual': p['stock'],
                'stock_minimo': 20
            }
        )
        if created:
            print(f"  ✅ {p['nombre']} - Bs/ {p['precio']}")

    # Productos - Postres
    productos_postres = [
        {'nombre': 'Helado', 'precio': Decimal('10.00'), 'stock': 40},
        {'nombre': 'Flan Casero', 'precio': Decimal('8.00'), 'stock': 30},
        {'nombre': 'Mousse de Chocolate', 'precio': Decimal('12.00'), 'stock': 25},
    ]

    for p in productos_postres:
        prod, created = Producto.objects.get_or_create(
            nombre=p['nombre'],
            defaults={
                'categoria': cat_postres,
                'precio': p['precio'],
                'disponible': True,
                'requiere_inventario': True,
                'stock_actual': p['stock'],
                'stock_minimo': 10
            }
        )
        if created:
            print(f"  ✅ {p['nombre']} - Bs/ {p['precio']}")

def crear_mesas():
    print("\n" + "="*50)
    print("CREANDO MESAS")
    print("="*50)

    # Crear 15 mesas
    for i in range(1, 16):
        mesa, created = Mesa.objects.get_or_create(
            numero=i,
            defaults={
                'capacidad': 4 if i <= 10 else 6,
                'estado': 'disponible',
                'disponible': True,
                'posicion_x': (i % 5) * 100,
                'posicion_y': (i // 5) * 100
            }
        )
        if created:
            print(f"  ✅ Mesa {i} - Capacidad: {mesa.capacidad} personas")

def main():
    print("\n" + "="*60)
    print("     CONFIGURACIÓN INICIAL DEL RESTAURANTE")
    print("="*60)

    crear_usuarios()
    crear_categorias_productos()
    crear_mesas()

    print("\n" + "="*60)
    print("✅ CONFIGURACIÓN COMPLETADA")
    print("="*60)

    print("\n📋 RESUMEN:")
    print(f"  • Usuarios creados: {Usuario.objects.count()}")
    print(f"  • Productos creados: {Producto.objects.count()}")
    print(f"  • Categorías creadas: {Categoria.objects.count()}")
    print(f"  • Mesas creadas: {Mesa.objects.count()}")

    print("\n🔑 CREDENCIALES DE ACCESO:")
    print("  • Admin: username='admin', password='admin123'")
    print("  • Cajero1: username='cajero1', PIN='1000'")
    print("  • Cajero2: username='cajero2', PIN='1001'")
    print("  • Mesero1: username='mesero1' (QR)")
    print("  • Cocinero1: username='cocinero1' (QR)")

    print("\n🚀 PRÓXIMOS PASOS:")
    print("  1. Inicia el servidor: python manage.py runserver")
    print("  2. Accede a http://127.0.0.1:8000/")
    print("  3. Inicia sesión con cajero (PIN: 1000) o admin")
    print("\n")

if __name__ == '__main__':
    main()
