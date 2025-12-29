#!/usr/bin/env python
"""
Script para listar todos los modelos registrados en Django Admin
SGIR v38.8

Útil para verificar qué modelos tienen URLs de admin válidas.
"""
import os
import sys
import django

# Configurar Django
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

django.setup()

from django.contrib import admin

print("=" * 60)
print("MODELOS REGISTRADOS EN DJANGO ADMIN")
print("=" * 60)
print()

modelos_registrados = []

for model, admin_instance in admin.site._registry.items():
    app_label = model._meta.app_label
    model_name = model._meta.model_name
    verbose_name = model._meta.verbose_name

    modelos_registrados.append({
        'app': app_label,
        'model': model_name,
        'verbose': verbose_name,
        'full': f"{app_label}.{model_name}"
    })

# Agrupar por app
apps_dict = {}
for modelo in modelos_registrados:
    app = modelo['app']
    if app not in apps_dict:
        apps_dict[app] = []
    apps_dict[app].append(modelo)

# Imprimir agrupado
for app_name in sorted(apps_dict.keys()):
    print(f"\n[{app_name.upper()}]")
    for modelo in sorted(apps_dict[app_name], key=lambda x: x['model']):
        print(f"   [OK] {modelo['model']:<30} -> admin:{app_name}_{modelo['model']}_changelist")

print()
print("=" * 60)
print(f"TOTAL: {len(modelos_registrados)} modelos registrados")
print("=" * 60)
