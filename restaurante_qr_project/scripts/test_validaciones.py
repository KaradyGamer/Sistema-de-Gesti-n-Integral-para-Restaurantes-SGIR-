# -*- coding: utf-8 -*-
"""
Script para probar validaciones de Producto
Verifica que no se puedan crear productos con valores negativos
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from app.productos.models import Producto, Categoria
from decimal import Decimal
from django.core.exceptions import ValidationError

def test_validaciones():
    print("=" * 80)
    print("PRUEBAS DE VALIDACION - PRODUCTO")
    print("=" * 80)

    # Obtener una categoría para las pruebas
    categoria = Categoria.objects.first()

    # TEST 1: Intentar crear producto con precio negativo
    print("\n[TEST 1] Intentar crear producto con precio NEGATIVO...")
    try:
        producto_negativo = Producto(
            nombre="Producto Test Negativo",
            precio=Decimal("-10.00"),
            categoria=categoria
        )
        producto_negativo.save()
        print("  [FALLO] El producto con precio negativo fue creado (NO DEBERIA)")
    except ValidationError as e:
        print("  [EXITO] Validacion funciono correctamente")
        print(f"  Error: {e.message_dict if hasattr(e, 'message_dict') else e}")
    except Exception as e:
        print(f"  [ERROR INESPERADO] {type(e).__name__}: {e}")

    # TEST 2: Intentar crear producto con precio cero
    print("\n[TEST 2] Intentar crear producto con precio CERO...")
    try:
        producto_cero = Producto(
            nombre="Producto Test Cero",
            precio=Decimal("0.00"),
            categoria=categoria
        )
        producto_cero.save()
        print("  [FALLO] El producto con precio cero fue creado (NO DEBERIA)")
    except ValidationError as e:
        print("  [EXITO] Validacion funciono correctamente")
        print(f"  Error: {e.message_dict if hasattr(e, 'message_dict') else e}")
    except Exception as e:
        print(f"  [ERROR INESPERADO] {type(e).__name__}: {e}")

    # TEST 3: Intentar crear producto con stock negativo
    print("\n[TEST 3] Intentar crear producto con stock NEGATIVO...")
    try:
        producto_stock_neg = Producto(
            nombre="Producto Test Stock Negativo",
            precio=Decimal("10.00"),
            stock_actual=-5,
            requiere_inventario=True,
            categoria=categoria
        )
        producto_stock_neg.save()
        print("  [FALLO] El producto con stock negativo fue creado (NO DEBERIA)")
    except ValidationError as e:
        print("  [EXITO] Validacion funciono correctamente")
        print(f"  Error: {e.message_dict if hasattr(e, 'message_dict') else e}")
    except Exception as e:
        print(f"  [ERROR INESPERADO] {type(e).__name__}: {e}")

    # TEST 4: Crear producto VALIDO (debería funcionar)
    print("\n[TEST 4] Crear producto VALIDO (precio y stock positivos)...")
    try:
        producto_valido = Producto(
            nombre="Producto Test Valido",
            precio=Decimal("15.50"),
            stock_actual=10,
            requiere_inventario=True,
            categoria=categoria
        )
        producto_valido.save()
        print("  [EXITO] Producto valido creado correctamente")
        print(f"  ID: {producto_valido.id}, Precio: {producto_valido.precio}, Stock: {producto_valido.stock_actual}")

        # Limpiar - eliminar el producto de prueba
        producto_valido.delete()
        print("  [LIMPIEZA] Producto de prueba eliminado")
    except ValidationError as e:
        print(f"  [ERROR] No deberia fallar: {e.message_dict if hasattr(e, 'message_dict') else e}")
    except Exception as e:
        print(f"  [ERROR INESPERADO] {type(e).__name__}: {e}")

    # TEST 5: Intentar modificar producto existente a precio negativo
    print("\n[TEST 5] Intentar modificar producto existente a precio NEGATIVO...")
    producto_test = Producto.objects.filter(activo=True).first()
    if producto_test:
        precio_original = producto_test.precio
        try:
            producto_test.precio = Decimal("-25.00")
            producto_test.save()
            print("  [FALLO] Modificacion a precio negativo fue permitida (NO DEBERIA)")
            # Revertir
            producto_test.precio = precio_original
            producto_test.save(skip_validation=True)
        except ValidationError as e:
            print("  [EXITO] Validacion funciono correctamente")
            print(f"  Error: {e.message_dict if hasattr(e, 'message_dict') else e}")
        except Exception as e:
            print(f"  [ERROR INESPERADO] {type(e).__name__}: {e}")
    else:
        print("  [SKIP] No hay productos para probar")

    # RESUMEN
    print("\n" + "=" * 80)
    print("RESUMEN DE PRUEBAS")
    print("=" * 80)
    print("Si todas las pruebas mostraron [EXITO], las validaciones funcionan correctamente.")
    print("Los productos con precios o stock negativos NO deberan poder guardarse.")
    print("=" * 80)

if __name__ == '__main__':
    test_validaciones()
