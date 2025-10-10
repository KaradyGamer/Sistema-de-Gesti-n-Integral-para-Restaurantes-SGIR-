#!/usr/bin/env python
"""
Script para actualizar mesas existentes con los nuevos campos
Ejecutar: python actualizar_mesas.py
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from app.mesas.models import Mesa

def actualizar_mesas():
    """Actualiza las mesas existentes con capacidad y posiciones"""

    mesas = Mesa.objects.all()

    if not mesas.exists():
        print("⚠️  No hay mesas en la base de datos.")
        print("   Crea algunas mesas desde el admin primero.")
        return

    print(f"📊 Actualizando {mesas.count()} mesas...")

    actualizadas = 0
    for i, mesa in enumerate(mesas):
        # Asignar capacidad por defecto si no tiene
        if mesa.capacidad == 0 or mesa.capacidad is None:
            mesa.capacidad = 4  # Capacidad por defecto

        # Asignar disponible
        mesa.disponible = True

        # Asignar posiciones para mapa (distribución en grid)
        # Calculamos posición en una cuadrícula 4x4
        fila = i // 4
        columna = i % 4
        mesa.posicion_x = columna * 200  # Espaciado horizontal
        mesa.posicion_y = fila * 150     # Espaciado vertical

        mesa.save()
        actualizadas += 1
        print(f"   ✅ Mesa {mesa.numero}: capacidad={mesa.capacidad}, pos=({mesa.posicion_x}, {mesa.posicion_y})")

    print(f"\n✅ {actualizadas} mesas actualizadas correctamente!")
    print("🗺️  El mapa de mesas está listo para usar.")

if __name__ == '__main__':
    print("=" * 50)
    print("🔧 ACTUALIZAR MESAS EXISTENTES")
    print("=" * 50)
    actualizar_mesas()
    print("=" * 50)