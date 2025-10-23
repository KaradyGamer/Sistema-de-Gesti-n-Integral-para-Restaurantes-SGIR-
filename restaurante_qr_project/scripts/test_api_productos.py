"""
Script temporal para verificar que devuelve la API de productos
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from app.productos.models import Producto
from django.conf import settings

# Simular lo que hace la vista lista_productos
productos = Producto.objects.filter(
    activo=True,
    disponible=True
).select_related('categoria').order_by('categoria__nombre', 'nombre')

print(f"Total productos: {productos.count()}")
print("\nProductos devueltos por la API:")
print("-" * 70)

for producto in productos:
    categoria_nombre = 'Sin Categoria' if not producto.categoria else producto.categoria.nombre
    print(f"ID: {producto.id:2d} | {producto.nombre:20s} | {categoria_nombre}")

print("\n" + "=" * 70)
print("Verificacion del producto 'Agua Mineral':")
agua = productos.filter(nombre__icontains='agua')
for p in agua:
    print(f"  - ID: {p.id}, Nombre: {p.nombre}")

# Verificar si existe producto con ID 19
print("\n" + "=" * 70)
print("Verificacion de ID 19:")
try:
    p19 = Producto.objects.get(id=19)
    print(f"  - EXISTE: ID 19 = {p19.nombre}, Activo: {p19.activo}, Disponible: {p19.disponible}")
except Producto.DoesNotExist:
    print("  - NO EXISTE producto con ID 19")

# Listar todos los productos incluyendo inactivos
print("\n" + "=" * 70)
print("Todos los productos (incluyendo inactivos):")
todos = Producto.objects.all().order_by('id')
for p in todos:
    status = "ACTIVO" if (p.activo and p.disponible) else "INACTIVO/NO_DISP"
    print(f"ID: {p.id:2d} | {p.nombre:20s} | {status}")
