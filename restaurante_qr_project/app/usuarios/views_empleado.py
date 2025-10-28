"""
Vistas para el panel unificado de empleados (meseros, cocineros)
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib import messages


@ensure_csrf_cookie
@login_required
def panel_empleado(request):
    """
    Panel unificado que muestra todas las áreas a las que el empleado tiene acceso
    """
    usuario = request.user
    print(f"[PANEL_EMPLEADO] Acceso de usuario: {usuario.username}, rol: {usuario.rol}")

    # Verificar que sea mesero o cocinero
    if usuario.rol not in ['mesero', 'cocinero']:
        print(f"[PANEL_EMPLEADO] Rol {usuario.rol} no permitido - redirigiendo a login")
        messages.error(request, 'No tienes permisos para acceder a este panel.')
        return redirect('/login/')

    print(f"[PANEL_EMPLEADO] Rol verificado OK - renderizando panel")

    # Obtener áreas activas del empleado
    areas_activas = usuario.get_areas_activas()

    # Definir información de cada área
    areas_info = {
        'mesero': {
            'nombre': 'Área de Mesero',
            'icono': '🍽️',
            'descripcion': 'Gestión de mesas, pedidos y atención al cliente',
            'url': '/mesero/',
            'color': '#667eea'
        },
        'cocina': {
            'nombre': 'Área de Cocina',
            'icono': '👨‍🍳',
            'descripcion': 'Gestión de pedidos en cocina y preparación',
            'url': '/cocina/',
            'color': '#f56565'
        },
        'caja': {
            'nombre': 'Área de Caja',
            'icono': '💰',
            'descripcion': 'Gestión de pagos y caja registradora',
            'url': '/caja/',
            'color': '#48bb78'
        },
        'reportes': {
            'nombre': 'Reportes',
            'icono': '📊',
            'descripcion': 'Visualización de reportes y estadísticas',
            'url': '/reportes/',
            'color': '#ed8936'
        }
    }

    # Crear lista de áreas disponibles
    areas_disponibles = []
    for area_key in areas_activas:
        if area_key in areas_info:
            area = areas_info[area_key].copy()
            area['key'] = area_key
            area['activa'] = True
            areas_disponibles.append(area)

    # Agregar áreas bloqueadas para mostrar
    todas_las_areas = ['mesero', 'cocina', 'caja', 'reportes']
    for area_key in todas_las_areas:
        if area_key not in areas_activas and area_key in areas_info:
            area = areas_info[area_key].copy()
            area['key'] = area_key
            area['activa'] = False
            areas_disponibles.append(area)

    context = {
        'usuario': usuario,
        'areas_disponibles': areas_disponibles,
        'total_areas_activas': len(areas_activas),
    }

    return render(request, 'empleado/panel_unificado.html', context)
