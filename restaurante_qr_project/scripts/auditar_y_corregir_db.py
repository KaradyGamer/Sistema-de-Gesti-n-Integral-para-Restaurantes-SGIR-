# -*- coding: utf-8 -*-
"""
Script de auditoria completa de la base de datos
Encuentra y corrige problemas con productos, precios y stock
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from app.productos.models import Producto

def auditar_y_corregir():
    """Audita todos los productos y corrige problemas automaticamente"""

    print("=" * 80)
    print("AUDITORIA DE BASE DE DATOS - PRODUCTOS")
    print("=" * 80)

    todos_productos = Producto.objects.all()
    total = todos_productos.count()

    print(f"\nTotal de productos en BD: {total}")
    print("-" * 80)

    # Contadores
    precios_negativos = 0
    stock_negativos = 0
    precios_cero = 0
    corregidos = 0

    print("\nREVISANDO Y CORRIGIENDO PRODUCTOS...")
    print("-" * 80)

    # Revisar y corregir cada producto
    for producto in todos_productos:
        cambios = []

        # Verificar precio negativo
        if producto.precio < 0:
            print(f"\n[CRITICO] ID {producto.id}: {producto.nombre}")
            print(f"  Precio negativo: Bs/ {float(producto.precio):.2f}")
            precios_negativos += 1

            # Corregir a positivo
            precio_anterior = float(producto.precio)
            producto.precio = abs(producto.precio)
            cambios.append(f"Precio: {precio_anterior:.2f} -> {float(producto.precio):.2f}")

        # Verificar stock negativo
        if producto.requiere_inventario and producto.stock_actual < 0:
            print(f"\n[CRITICO] ID {producto.id}: {producto.nombre}")
            print(f"  Stock negativo: {producto.stock_actual}")
            stock_negativos += 1

            # Corregir a 0
            stock_anterior = producto.stock_actual
            producto.stock_actual = 0
            cambios.append(f"Stock: {stock_anterior} -> {producto.stock_actual}")

        # Verificar precio en cero
        if producto.precio == 0:
            print(f"\n[ADVERTENCIA] ID {producto.id}: {producto.nombre}")
            print(f"  Precio en cero")
            precios_cero += 1

            # Marcar como no disponible
            if producto.disponible:
                producto.disponible = False
                cambios.append("Marcado como no disponible")

        # Guardar cambios si los hay
        if cambios:
            try:
                producto.save()
                print(f"  CORREGIDO: {', '.join(cambios)}")
                corregidos += 1
            except Exception as e:
                print(f"  ERROR al guardar: {e}")

    # Resumen
    print("\n" + "=" * 80)
    print("RESUMEN DE AUDITORIA")
    print("=" * 80)
    print(f"Total productos revisados: {total}")
    print(f"Productos con precio negativo: {precios_negativos}")
    print(f"Productos con stock negativo: {stock_negativos}")
    print(f"Productos con precio en cero: {precios_cero}")
    print(f"Total de productos corregidos: {corregidos}")
    print("=" * 80)

    # Verificacion final
    print("\n\nVERIFICACION FINAL...")
    print("-" * 80)

    verificar_negativos = Producto.objects.filter(precio__lt=0).count()
    verificar_stock_neg = Producto.objects.filter(requiere_inventario=True, stock_actual__lt=0).count()

    print(f"Productos con precio negativo restantes: {verificar_negativos}")
    print(f"Productos con stock negativo restantes: {verificar_stock_neg}")

    if verificar_negativos == 0 and verificar_stock_neg == 0:
        print("\n*** BASE DE DATOS CORREGIDA EXITOSAMENTE ***")
    else:
        print("\n*** ADVERTENCIA: AUN HAY PROBLEMAS POR CORREGIR ***")

    # Mostrar productos disponibles actualmente
    print("\n\nPRODUCTOS ACTIVOS Y DISPONIBLES:")
    print("-" * 80)
    productos_activos = Producto.objects.filter(activo=True, disponible=True).order_by('nombre')
    for p in productos_activos:
        stock_info = f"Stock: {p.stock_actual}" if p.requiere_inventario else "Sin inventario"
        print(f"ID {p.id:2d} | {p.nombre:25s} | Bs/ {float(p.precio):7.2f} | {stock_info}")

    print("\n" + "=" * 80)
    print("AUDITORIA COMPLETADA")
    print("=" * 80)

if __name__ == '__main__':
    auditar_y_corregir()
