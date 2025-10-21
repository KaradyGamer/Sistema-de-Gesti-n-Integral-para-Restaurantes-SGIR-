from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Sum
from datetime import date, datetime

# Importar decoradores personalizados
from app.usuarios.decorators import rol_requerido, solo_cajero

from app.pedidos.models import Pedido
from app.mesas.models import Mesa
from app.productos.models import Producto
from .models import Transaccion, CierreCaja, AlertaStock, HistorialModificacion
from .utils import (
    obtener_pedidos_pendientes_pago,
    verificar_alertas_stock,
    obtener_estadisticas_caja_dia
)


# ──────────────────────────────────────────────
# 🧾 PANEL PRINCIPAL DEL CAJERO
# ──────────────────────────────────────────────

@solo_cajero
def panel_unificado(request):
    """
    Panel unificado moderno con sidebar - Versión SPA
    """
    from .models import JornadaLaboral

    # Verificar si hay un turno abierto
    turno_abierto = CierreCaja.objects.filter(
        cajero=request.user,
        estado='abierto',
        fecha=date.today()
    ).first()

    # Verificar jornada laboral
    jornada_activa = JornadaLaboral.jornada_activa()

    # Estadísticas del día
    estadisticas = obtener_estadisticas_caja_dia()

    context = {
        'user': request.user,
        'nombre_usuario': request.user.get_full_name() or request.user.username,
        'user_role': request.user.rol,
        'turno_abierto': turno_abierto,
        'jornada_activa': jornada_activa,
        'estadisticas': estadisticas,
    }

    return render(request, 'cajero/panel_unificado.html', context)


@solo_cajero
def panel_caja(request):
    """
    Panel principal del cajero con vista general de pedidos pendientes de pago
    """

    # Verificar si hay un turno abierto
    turno_abierto = CierreCaja.objects.filter(
        cajero=request.user,
        estado='abierto',
        fecha=date.today()
    ).first()

    # Obtener pedidos pendientes de pago (todos los estados excepto cancelados)
    # El cajero puede ver pedidos en cualquier estado para cobrar y modificar
    pedidos_pendientes = Pedido.objects.filter(
        estado_pago='pendiente'
    ).exclude(
        estado='cancelado'
    ).select_related('mesa').prefetch_related('detalles__producto').order_by('-fecha')

    # Obtener alertas de stock activas
    alertas_stock = AlertaStock.objects.filter(
        estado='activa'
    ).select_related('producto').order_by('-fecha_creacion')[:5]

    # Estadísticas del día
    estadisticas = obtener_estadisticas_caja_dia()

    context = {
        'user': request.user,
        'nombre_usuario': request.user.first_name or request.user.username,
        'title': 'Panel de Caja',
        'user_role': 'cajero',
        'turno_abierto': turno_abierto,
        'pedidos_pendientes': pedidos_pendientes,
        'alertas_stock': alertas_stock,
        'estadisticas': estadisticas,
    }

    return render(request, 'cajero/panel_caja.html', context)


# ──────────────────────────────────────────────
# 💰 DETALLE DE PEDIDO Y PAGO
# ──────────────────────────────────────────────

@login_required
def detalle_pedido(request, pedido_id):
    """
    Vista detallada de un pedido específico para procesar el pago
    """
    if request.user.rol not in ['cajero', 'admin', 'gerente']:
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('/caja/')

    pedido = get_object_or_404(
        Pedido.objects.select_related('mesa').prefetch_related('detalles__producto'),
        id=pedido_id
    )

    # Calcular totales
    total_final = pedido.total_final if pedido.total_final > 0 else pedido.total

    context = {
        'user': request.user,
        'title': f'Pedido #{pedido.id}',
        'pedido': pedido,
        'total_final': total_final,
    }

    return render(request, 'cajero/detalle_pedido.html', context)


@login_required
def procesar_pago(request, pedido_id):
    """
    Formulario para procesar el pago de un pedido
    """
    if request.user.rol not in ['cajero', 'admin', 'gerente']:
        messages.error(request, 'No tienes permisos para procesar pagos.')
        return redirect('/caja/')

    pedido = get_object_or_404(
        Pedido.objects.select_related('mesa').prefetch_related('detalles__producto'),
        id=pedido_id
    )

    # Verificar que el pedido esté en estado correcto
    if pedido.estado_pago == 'pagado':
        messages.warning(request, 'Este pedido ya ha sido pagado.')
        return redirect('panel_caja')

    # Calcular total final
    total_final = pedido.total_final if pedido.total_final > 0 else pedido.total

    context = {
        'user': request.user,
        'title': f'Procesar Pago - Pedido #{pedido.id}',
        'pedido': pedido,
        'total_final': total_final,
    }

    return render(request, 'cajero/procesar_pago.html', context)


# ──────────────────────────────────────────────
# 📊 MAPA DIGITAL DE MESAS
# ──────────────────────────────────────────────

@login_required
def mapa_mesas(request):
    """
    Vista del mapa digital de mesas con estados en tiempo real
    ✅ ACTUALIZADO: Igual que vista de mesero - muestra TODAS las mesas
    """
    if request.user.rol not in ['cajero', 'admin', 'gerente', 'mesero']:
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('/caja/')

    # ✅ CORREGIDO: Obtener TODAS las mesas (no solo disponibles)
    mesas = Mesa.objects.all().order_by('numero')

    # Agregar información de pedidos a cada mesa
    mesas_con_info = []
    for mesa in mesas:
        # Buscar pedidos activos de la mesa
        pedidos_activos = Pedido.objects.filter(
            mesa=mesa,
            estado_pago='pendiente'
        ).order_by('-fecha')

        total_pendiente = sum(
            p.total_final if p.total_final > 0 else p.total
            for p in pedidos_activos
        )

        mesas_con_info.append({
            'mesa': mesa,
            'pedidos_activos': pedidos_activos,
            'total_pendiente': total_pendiente,
            'cantidad_pedidos': pedidos_activos.count(),
        })

    context = {
        'user': request.user,
        'title': 'Mapa de Mesas',
        'mesas_con_info': mesas_con_info,
    }

    return render(request, 'cajero/mapa_mesas.html', context)


# ──────────────────────────────────────────────
# 📜 HISTORIAL DE TRANSACCIONES
# ──────────────────────────────────────────────

@login_required
def historial_transacciones(request):
    """
    Vista del historial de transacciones con filtros
    """
    if request.user.rol not in ['cajero', 'admin', 'gerente']:
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('/caja/')

    # Obtener parámetros de filtro
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    metodo_pago = request.GET.get('metodo_pago')
    mesa = request.GET.get('mesa')

    # Query base
    transacciones = Transaccion.objects.select_related(
        'pedido__mesa', 'cajero'
    ).order_by('-fecha_hora')

    # Aplicar filtros
    if fecha_inicio:
        try:
            fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            transacciones = transacciones.filter(fecha_hora__date__gte=fecha_inicio_dt)
        except ValueError:
            pass

    if fecha_fin:
        try:
            fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
            transacciones = transacciones.filter(fecha_hora__date__lte=fecha_fin_dt)
        except ValueError:
            pass

    if metodo_pago:
        transacciones = transacciones.filter(metodo_pago=metodo_pago)

    if mesa:
        transacciones = transacciones.filter(pedido__mesa__numero=mesa)

    # Paginación simple (últimas 50 transacciones)
    transacciones = transacciones[:50]

    # Calcular totales
    total_general = transacciones.aggregate(Sum('monto_total'))['monto_total__sum'] or 0

    context = {
        'user': request.user,
        'title': 'Historial de Transacciones',
        'transacciones': transacciones,
        'total_general': total_general,
        'filtros': {
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'metodo_pago': metodo_pago,
            'mesa': mesa,
        }
    }

    return render(request, 'cajero/historial.html', context)


# ──────────────────────────────────────────────
# 💼 CIERRE DE CAJA
# ──────────────────────────────────────────────

@login_required
def abrir_caja(request):
    """
    Vista para abrir un turno de caja
    """
    if request.user.rol not in ['cajero', 'admin', 'gerente']:
        messages.error(request, 'No tienes permisos para abrir caja.')
        return redirect('/caja/')

    # Verificar si ya hay un turno abierto
    turno_existente = CierreCaja.objects.filter(
        cajero=request.user,
        estado='abierto',
        fecha=date.today()
    ).first()

    if turno_existente:
        messages.warning(request, 'Ya tienes un turno abierto.')
        context = {
            'user': request.user,
            'title': 'Abrir Caja',
            'caja_abierta': turno_existente,
        }
        return render(request, 'cajero/abrir_caja.html', context)

    # Manejar POST (crear apertura)
    if request.method == 'POST':
        try:
            turno = request.POST.get('turno')
            efectivo_inicial = request.POST.get('efectivo_inicial', 0)

            # Validaciones
            if not turno:
                messages.error(request, 'Debes seleccionar un turno.')
                return redirect('/caja/abrir/')

            try:
                efectivo_inicial = float(efectivo_inicial)
                if efectivo_inicial < 0:
                    raise ValueError()
            except ValueError:
                messages.error(request, 'El efectivo inicial debe ser un número válido.')
                return redirect('/caja/abrir/')

            # Crear apertura de caja
            cierre = CierreCaja.objects.create(
                cajero=request.user,
                fecha=date.today(),
                turno=turno,
                estado='abierto',
                efectivo_inicial=efectivo_inicial,
                efectivo_esperado=efectivo_inicial
            )

            messages.success(request, f'Caja abierta exitosamente para turno {turno.upper()}.')
            return redirect('/caja/')

        except Exception as e:
            messages.error(request, f'Error al abrir caja: {str(e)}')
            return redirect('/caja/abrir/')

    # GET - Mostrar formulario
    context = {
        'user': request.user,
        'title': 'Abrir Caja',
        'hoy': date.today(),
        'ahora': timezone.now(),
    }

    return render(request, 'cajero/abrir_caja.html', context)


@login_required
def cierre_caja(request):
    """
    Vista para cerrar el turno de caja y hacer cuadre
    """
    if request.user.rol not in ['cajero', 'admin', 'gerente']:
        messages.error(request, 'No tienes permisos para cerrar caja.')
        return redirect('/caja/')

    # Obtener turno abierto
    turno_abierto = CierreCaja.objects.filter(
        cajero=request.user,
        estado='abierto',
        fecha=date.today()
    ).first()

    if not turno_abierto:
        messages.error(request, 'No tienes un turno abierto para cerrar.')
        return redirect('panel_caja')

    # Obtener transacciones del turno
    transacciones = Transaccion.objects.filter(
        cajero=request.user,
        fecha_hora__date=date.today(),
        estado='procesado'
    )

    # Calcular totales por método
    from .utils import calcular_totales_caja
    totales = calcular_totales_caja(transacciones)

    # Calcular efectivo esperado
    efectivo_esperado = turno_abierto.efectivo_inicial + totales['efectivo']

    context = {
        'user': request.user,
        'title': 'Cierre de Caja',
        'turno': turno_abierto,
        'transacciones': transacciones,
        'totales': totales,
        'efectivo_esperado': efectivo_esperado,
        'numero_transacciones': transacciones.count(),
    }

    return render(request, 'cajero/cierre_caja.html', context)


# ──────────────────────────────────────────────
# ✏️ MODIFICAR PEDIDO
# ──────────────────────────────────────────────

@login_required
def modificar_pedido(request, pedido_id):
    """
    Vista para modificar un pedido (agregar/eliminar productos, cambiar cantidades)
    """
    if request.user.rol not in ['cajero', 'admin', 'gerente']:
        messages.error(request, 'No tienes permisos para modificar pedidos.')
        return redirect('/caja/')

    pedido = get_object_or_404(
        Pedido.objects.select_related('mesa').prefetch_related('detalles__producto'),
        id=pedido_id
    )

    # Verificar que el pedido no esté pagado
    if pedido.estado_pago == 'pagado':
        messages.error(request, 'No se puede modificar un pedido ya pagado.')
        return redirect('detalle_pedido', pedido_id=pedido_id)

    # Obtener todos los productos disponibles y activos
    productos = Producto.objects.filter(disponible=True, activo=True).order_by('nombre')

    # Obtener items del pedido con información completa
    items = []
    for detalle in pedido.detalles.all():
        items.append({
            'id': detalle.id,
            'producto': detalle.producto,
            'cantidad': detalle.cantidad,
            'precio_unitario': detalle.producto.precio,
            'subtotal': detalle.subtotal
        })

    context = {
        'user': request.user,
        'title': f'Modificar Pedido #{pedido.id}',
        'pedido': pedido,
        'items': items,
        'productos_disponibles': productos,
    }

    return render(request, 'cajero/modificar_pedido.html', context)


# ──────────────────────────────────────────────
# 🔄 REASIGNAR PEDIDO A OTRA MESA
# ──────────────────────────────────────────────

@login_required
def reasignar_pedido(request, pedido_id):
    """
    Vista para reasignar un pedido a otra mesa
    """
    if request.user.rol not in ['cajero', 'admin', 'gerente']:
        messages.error(request, 'No tienes permisos para reasignar pedidos.')
        return redirect('/caja/')

    pedido = get_object_or_404(Pedido, id=pedido_id)

    # Verificar que el pedido no esté pagado
    if pedido.estado_pago == 'pagado':
        messages.error(request, 'No se puede reasignar un pedido ya pagado.')
        return redirect('detalle_pedido', pedido_id=pedido_id)

    # Obtener todas las mesas disponibles
    mesas = Mesa.objects.filter(disponible=True).order_by('numero')

    context = {
        'user': request.user,
        'title': f'Reasignar Pedido #{pedido.id}',
        'pedido': pedido,
        'mesas': mesas,
    }

    return render(request, 'cajero/reasignar_pedido.html', context)


# ──────────────────────────────────────────────
# 📊 ALERTAS DE STOCK
# ──────────────────────────────────────────────

@login_required
def alertas_stock_view(request):
    """
    Vista de todas las alertas de stock
    """
    if request.user.rol not in ['cajero', 'admin', 'gerente']:
        messages.error(request, 'No tienes permisos para ver alertas.')
        return redirect('/caja/')

    # Obtener alertas activas
    alertas_activas = AlertaStock.objects.filter(
        estado='activa'
    ).select_related('producto').order_by('-fecha_creacion')

    # Obtener alertas resueltas (últimas 20)
    alertas_resueltas = AlertaStock.objects.filter(
        estado='resuelta'
    ).select_related('producto', 'resuelto_por').order_by('-fecha_resolucion')[:20]

    context = {
        'user': request.user,
        'title': 'Alertas de Stock',
        'alertas_activas': alertas_activas,
        'alertas_resueltas': alertas_resueltas,
    }

    return render(request, 'cajero/alertas_stock.html', context)


# ──────────────────────────────────────────────
# 👥 MÓDULO DE PERSONAL (NUEVO)
# ──────────────────────────────────────────────

@solo_cajero
def personal_panel(request):
    """
    Panel de gestión de personal - Lista de empleados para generar QR
    """

    from app.usuarios.models import Usuario

    # Obtener solo meseros y cocineros activos (no incluir admin, gerente, cajero)
    empleados = Usuario.objects.filter(
        rol__in=['mesero', 'cocinero'],
        activo=True
    ).order_by('rol', 'first_name', 'last_name')

    # Separar por rol
    meseros = empleados.filter(rol='mesero')
    cocineros = empleados.filter(rol='cocinero')

    context = {
        'user': request.user,
        'title': 'Gestión de Personal',
        'meseros': meseros,
        'cocineros': cocineros,
        'total_empleados': empleados.count(),
    }

    return render(request, 'cajero/personal_panel.html', context)


@login_required
def generar_qr_empleado(request, empleado_id):
    """
    Genera un código QR único para que un empleado acceda al sistema
    """
    if request.user.rol != 'cajero':
        return JsonResponse({'error': 'No autorizado'}, status=403)

    from app.usuarios.models import Usuario
    import qrcode
    from io import BytesIO
    import base64

    try:
        empleado = get_object_or_404(Usuario, id=empleado_id)

        # Verificar que sea mesero o cocinero
        if empleado.rol not in ['mesero', 'cocinero']:
            return JsonResponse({'error': 'Solo se puede generar QR para meseros y cocineros'}, status=400)

        if not empleado.activo:
            return JsonResponse({'error': 'El empleado está inactivo'}, status=400)

        # Generar nuevo token QR (SIEMPRE regenerar para tener URL actualizada)
        token = empleado.generar_qr_token()

        # Crear URL de autenticación usando variable de entorno
        from django.conf import settings
        from decouple import config

        # Obtener host configurado o usar el del request
        qr_host = config('QR_HOST', default=request.get_host())

        qr_url = f"{request.scheme}://{qr_host}/usuarios/auth-qr/{token}/"

        # Generar código QR
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convertir imagen a base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return JsonResponse({
            'success': True,
            'qr_image': f'data:image/png;base64,{img_str}',
            'empleado': empleado.get_full_name() or empleado.username,
            'rol': empleado.get_rol_display(),
            'token': str(token),
            'url': qr_url
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ══════════════════════════════════════════════
# 📅 GESTIÓN DE JORNADA LABORAL (NUEVO)
# ══════════════════════════════════════════════

@solo_cajero
def gestionar_jornada(request):
    """
    Vista para activar/desactivar la jornada laboral
    Solo el cajero puede gestionar la jornada
    """

    from .models import JornadaLaboral

    # Obtener jornada activa si existe
    jornada_activa = JornadaLaboral.jornada_activa()

    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'iniciar':
            # Verificar que no haya jornada activa
            if JornadaLaboral.hay_jornada_activa():
                messages.error(request, 'Ya hay una jornada activa. Debes finalizarla antes de iniciar una nueva.')
                return redirect('/caja/jornada/')

            # Crear nueva jornada
            observaciones = request.POST.get('observaciones_apertura', '')
            jornada = JornadaLaboral.objects.create(
                cajero=request.user,
                observaciones_apertura=observaciones
            )
            messages.success(request, f'✅ Jornada laboral iniciada exitosamente a las {jornada.hora_inicio.strftime("%H:%M")}')
            return redirect('/caja/')

        elif accion == 'finalizar':
            # Verificar que haya jornada activa
            if not jornada_activa:
                messages.error(request, 'No hay ninguna jornada activa para finalizar.')
                return redirect('/caja/jornada/')

            # Finalizar jornada
            observaciones = request.POST.get('observaciones_cierre', '')
            jornada_activa.finalizar(request.user, observaciones)
            messages.success(request, f'✅ Jornada laboral finalizada exitosamente a las {jornada_activa.hora_fin.strftime("%H:%M")}')
            return redirect('/caja/')

    context = {
        'user': request.user,
        'title': 'Gestión de Jornada Laboral',
        'jornada_activa': jornada_activa,
    }

    return render(request, 'cajero/gestionar_jornada.html', context)


# ──────────────────────────────────────────────
# 📊 API - ESTADÍSTICAS DEL DÍA
# ──────────────────────────────────────────────

@solo_cajero
def estadisticas_dia_api(request):
    """
    API para obtener estadísticas del día en tiempo real
    Usado por el panel unificado para actualizar datos
    """
    from datetime import date

    hoy = date.today()

    # Pedidos del día
    pedidos_hoy = Pedido.objects.filter(fecha__date=hoy)
    total_pedidos = pedidos_hoy.count()
    pedidos_pagados = pedidos_hoy.filter(estado_pago='pagado').count()
    pedidos_pendientes = pedidos_hoy.filter(estado_pago='pendiente').count()

    # Ingresos del día
    ingresos_totales = pedidos_hoy.filter(estado_pago='pagado').aggregate(
        total=Sum('total')
    )['total'] or 0

    # Pedidos por estado
    pendientes = pedidos_hoy.filter(estado='pendiente').count()
    en_preparacion = pedidos_hoy.filter(estado='en_preparacion').count()
    listos = pedidos_hoy.filter(estado='listo').count()
    entregados = pedidos_hoy.filter(estado='entregado').count()

    # Mesas ocupadas
    mesas_ocupadas = Mesa.objects.filter(estado='ocupada').count()
    mesas_totales = Mesa.objects.count()

    return JsonResponse({
        'success': True,
        'estadisticas': {
            'total_pedidos': total_pedidos,
            'pedidos_pagados': pedidos_pagados,
            'pedidos_pendientes': pedidos_pendientes,
            'ingresos_totales': float(ingresos_totales),
            'pedidos_por_estado': {
                'pendientes': pendientes,
                'en_preparacion': en_preparacion,
                'listos': listos,
                'entregados': entregados,
            },
            'mesas': {
                'ocupadas': mesas_ocupadas,
                'totales': mesas_totales,
                'porcentaje': round((mesas_ocupadas / mesas_totales * 100) if mesas_totales > 0 else 0, 1)
            }
        }
    })
