# -*- coding: utf-8 -*-
"""
Script para corregir DetallePedido con precios negativos
Los pedidos antiguos guardaron precios negativos que causan errores
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from app.pedidos.models import DetallePedido, Pedido
from decimal import Decimal

def corregir_detalles_pedido():
    print("=" * 80)
    print("CORRIGIENDO DETALLEPEDIDO CON PRECIOS NEGATIVOS")
    print("=" * 80)

    # Buscar detalles con precio negativo
    detalles_negativos = DetallePedido.objects.filter(precio_unitario__lt=0)
    total = detalles_negativos.count()

    print(f"\nDetalles con precio negativo encontrados: {total}")
    print("-" * 80)

    if total == 0:
        print("\n*** NO SE ENCONTRARON DETALLES CON PRECIOS NEGATIVOS ***")
        return

    corregidos = 0

    for detalle in detalles_negativos:
        try:
            pedido = detalle.pedido
            producto = detalle.producto
            precio_anterior = float(detalle.precio_unitario)

            print(f"\n[Pedido #{pedido.id}] {producto.nombre}")
            print(f"  Precio negativo: Bs/ {precio_anterior:.2f}")

            # Corregir a positivo
            detalle.precio_unitario = abs(detalle.precio_unitario)

            # Recalcular subtotal
            detalle.subtotal = detalle.precio_unitario * detalle.cantidad

            detalle.save()

            print(f"  CORREGIDO: Precio → Bs/ {float(detalle.precio_unitario):.2f}")
            print(f"  Subtotal recalculado: Bs/ {float(detalle.subtotal):.2f}")

            corregidos += 1

            # Recalcular total del pedido
            pedido.calcular_totales()
            pedido.save()
            print(f"  Total del pedido actualizado: Bs/ {float(pedido.total):.2f}")

        except Exception as e:
            print(f"  ERROR: {type(e).__name__}: {e}")

    print("\n" + "=" * 80)
    print(f"RESUMEN: {corregidos}/{total} detalles corregidos")
    print("=" * 80)

    # Verificación final
    verificar_negativos = DetallePedido.objects.filter(precio_unitario__lt=0).count()

    if verificar_negativos == 0:
        print("\n*** TODOS LOS DETALLES CORREGIDOS EXITOSAMENTE ***")
    else:
        print(f"\n*** ADVERTENCIA: AUN HAY {verificar_negativos} DETALLES CON PRECIOS NEGATIVOS ***")

if __name__ == '__main__':
    corregir_detalles_pedido()
