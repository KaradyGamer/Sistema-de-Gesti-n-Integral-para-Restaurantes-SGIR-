from django.shortcuts import render, redirect
from django.utils import timezone
from django.http import JsonResponse
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from datetime import date, datetime, timedelta
import logging

from .models import Pedido, DetallePedido
from .serializers import PedidoSerializer
from app.mesas.models import Mesa
from app.productos.models import Producto
from app.usuarios.permisos import EsCocinero, EsMesero
from app.reservas.models import Reserva

from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie

#  Configurar logger
logger = logging.getLogger('app.pedidos')

# 
#  Cliente  Plantillas pblicas
# 

def formulario_cliente(request):
    """Formulario de pedido - puede recibir mesa predeterminada desde mapa"""
    #  NUEVO: Obtener mesa desde parmetro URL (?mesa=5)
    mesa_numero = request.GET.get('mesa', None)

    #  NUEVO: Pasar usuario si est autenticado (para meseros)
    context = {
        'mesa_numero': mesa_numero,
        'usuario_id': request.user.id if request.user.is_authenticated else None,
        'es_mesero': request.user.is_authenticated
    }

    return render(request, 'cliente/formulario.html', context)

def vista_exito(request):
    return render(request, 'cliente/exito.html')

def confirmacion_pedido(request):
    context = {
        'usuario_id': request.user.id if request.user.is_authenticated else None,
    }
    return render(request, 'cliente/confirmacion.html', context)

# ══════════════════════════════════════════════
# 🧾 SGIR v40.4.0: CREAR PEDIDO CON CUENTAMESA
# ══════════════════════════════════════════════
@api_view(['POST'])
@authentication_classes([])  # Sin autenticación = sin CSRF
@permission_classes([AllowAny])
@transaction.atomic  # Garantiza atomicidad de la transacción
def crear_pedido_cliente(request):
    """
    Crear pedido desde el cliente - VERSIÓN v40.4.0 CON CUENTAMESA

    Cambios v40.4.0:
    - Usa CuentaMesa como entidad financiera central
    - Permite múltiples pedidos por mesa
    - Descuenta stock UNA sola vez (al crear)
    - Validación anticipada (fail-fast)
    - Rollback automático
    """
    try:
        from django.db.models import F
        from django.core.exceptions import ValidationError
        from app.caja.models import CuentaMesa

        logger.info("=== CREAR PEDIDO v40.4.0 ===")

        # ===== 1. EXTRACCIÓN DE DATOS =====
        mesa_id = request.data.get('mesa_id') or request.data.get('mesa') or request.data.get('numero_mesa')
        productos_data = request.data.get('productos') or request.data.get('detalles') or []
        forma_pago = request.data.get('forma_pago', 'efectivo')
        mesero_id = request.data.get('mesero_id') or request.data.get('usuario_id')
        numero_personas = request.data.get('numero_personas')

        # ===== 2. VALIDACIONES INICIALES =====
        if not mesa_id:
            return Response({'error': 'El número de mesa es requerido'}, status=status.HTTP_400_BAD_REQUEST)

        if not productos_data or len(productos_data) == 0:
            return Response({'error': 'Debe incluir al menos un producto en el pedido'}, status=status.HTTP_400_BAD_REQUEST)

        if not numero_personas or int(numero_personas) < 1:
            return Response({'error': 'El número de personas debe ser al menos 1'}, status=status.HTTP_400_BAD_REQUEST)

        numero_personas = int(numero_personas)

        # ===== 3. LOCK DE MESA =====
        try:
            mesa = Mesa.objects.select_for_update().get(numero=mesa_id)
        except Mesa.DoesNotExist:
            try:
                mesa = Mesa.objects.select_for_update().get(id=mesa_id)
            except Mesa.DoesNotExist:
                return Response({'error': f'Mesa {mesa_id} no encontrada'}, status=status.HTTP_404_NOT_FOUND)

        # Validar capacidad
        capacidad_real = mesa.capacidad_combinada if mesa.es_combinada else mesa.capacidad
        if numero_personas > capacidad_real:
            return Response({
                'error': f'Mesa {mesa.numero} solo tiene capacidad para {capacidad_real} personas. Solicitado: {numero_personas}'
            }, status=status.HTTP_400_BAD_REQUEST)

        # ===== 4. OBTENER O CREAR CUENTAMESA ABIERTA =====
        cuenta = CuentaMesa.objects.select_for_update().filter(mesa=mesa, estado='abierta').first()

        if not cuenta:
            from app.usuarios.models import Usuario
            mesero = None
            if mesero_id:
                try:
                    mesero = Usuario.objects.get(id=mesero_id)
                except Usuario.DoesNotExist:
                    pass

            cuenta = CuentaMesa.objects.create(
                mesa=mesa,
                estado='abierta',
                total_acumulado=0,
                monto_pagado=0,
                abierta_por=mesero or (request.user if request.user.is_authenticated else None)
            )
            logger.info(f"✅ Nueva CuentaMesa creada para Mesa {mesa.numero}")
        else:
            logger.info(f"♻️  Usando CuentaMesa existente para Mesa {mesa.numero}")

        # ===== 5. OBTENER MESERO =====
        mesero = cuenta.abierta_por
        if mesero_id:
            from app.usuarios.models import Usuario
            try:
                mesero_nuevo = Usuario.objects.get(id=mesero_id)
                mesero = mesero_nuevo
            except Usuario.DoesNotExist:
                pass

        # ===== 6. VALIDACIÓN ANTICIPADA DE PRODUCTOS (FAIL-FAST) =====
        productos_ids = []
        productos_cantidades = {}

        for item in productos_data:
            producto_id = item.get('producto_id') or item.get('producto') or item.get('id')
            cantidad = int(item.get('cantidad', 1))
            if producto_id:
                productos_ids.append(producto_id)
                productos_cantidades[producto_id] = cantidad

        if not productos_ids:
            raise ValidationError('Debe incluir al menos un producto válido en el pedido')

        productos = Producto.objects.select_for_update().filter(id__in=productos_ids)
        productos_map = {p.id: p for p in productos}

        for producto_id, cantidad in productos_cantidades.items():
            if producto_id not in productos_map:
                raise ValidationError(f'Producto ID {producto_id} no encontrado')

            producto = productos_map[producto_id]

            if producto.requiere_inventario and producto.stock_actual < cantidad:
                raise ValidationError(
                    f'Stock insuficiente de {producto.nombre}. '
                    f'Disponible: {producto.stock_actual}, Solicitado: {cantidad}'
                )

        # ===== 7. CREAR PEDIDO =====
        pedido = Pedido.objects.create(
            mesa=mesa,
            cuenta=cuenta,
            fecha=timezone.now(),
            forma_pago=forma_pago,
            estado='pendiente',
            mesero_comanda=mesero,
            numero_personas=numero_personas
        )

        # ===== 8. DESCONTAR STOCK Y CREAR DETALLES =====
        total_calculado = 0
        detalles_creados = []

        for item in productos_data:
            producto_id = item.get('producto_id') or item.get('producto') or item.get('id')
            cantidad = int(item.get('cantidad', 1))

            if not producto_id or producto_id not in productos_map:
                continue

            producto = productos_map[producto_id]

            if producto.requiere_inventario:
                updated = Producto.objects.filter(
                    id=producto.id,
                    stock_actual__gte=cantidad
                ).update(stock_actual=F('stock_actual') - cantidad)

                if updated == 0:
                    raise ValidationError(
                        f'Stock insuficiente de {producto.nombre} (race condition detectada)'
                    )

                producto.refresh_from_db()

            subtotal = producto.precio * cantidad
            total_calculado += subtotal

            DetallePedido.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=producto.precio,
                subtotal=subtotal
            )

            detalles_creados.append({
                'producto': producto.nombre,
                'cantidad': cantidad,
                'precio_unitario': float(producto.precio),
                'subtotal': float(subtotal),
                'stock_restante': producto.stock_actual if producto.requiere_inventario else None
            })

        # ===== 9. ACTUALIZAR TOTALES =====
        pedido.total = total_calculado
        pedido.total_final = total_calculado
        pedido.save()

        # ===== 10. RECALCULAR CUENTA =====
        cuenta.recalcular_totales()

        # ===== 11. CAMBIAR ESTADO DE MESA =====
        if mesa.estado != 'ocupada':
            mesa.estado = 'ocupada'
            mesa.save()

        # ===== 12. RESPUESTA =====
        logger.info(f"✅ Pedido #{pedido.id} creado - Mesa {mesa.numero} - Total: Bs/ {total_calculado} - Cuenta #{cuenta.id}")

        return Response({
            'success': True,
            'mensaje': 'Pedido creado exitosamente',
            'pedido_id': pedido.id,
            'cuenta_id': cuenta.id,
            'mesa': mesa.numero,
            'numero_personas': numero_personas,
            'mesero': f"{mesero.first_name} {mesero.last_name}" if mesero else "Cliente directo",
            'total': float(total_calculado),
            'cuenta_total_acumulado': float(cuenta.total_acumulado),
            'detalles': detalles_creados,
            'estado': pedido.estado
        }, status=status.HTTP_201_CREATED)

    except ValidationError as e:
        # ✅ FIX #2 v40.3.2: Capturar errores de validación (rollback automático por @transaction.atomic)
        logger.warning(f"Validación fallida creando pedido: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.exception(f"Error grave creando pedido: {str(e)}")
        return Response({
            'error': f'Error interno del servidor: {str(e)}',
            'debug': 'Ver consola del servidor para detalles'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#
#  Cocinero  Vistas HTML
#

#  Panel cocinero (requiere autenticacin y rol)
@ensure_csrf_cookie
def panel_cocina(request):
    """Panel del cocinero - Sin decoradores Django"""
    if not request.user.is_authenticated:
        messages.warning(request, 'Debes iniciar sesin para acceder al panel de cocina.')
        return redirect('/login/')
    
    return render(request, 'cocinero/panel_cocina.html', {
        'title': 'Panel del Cocinero',
        'user_role': 'cocinero',
        'user': request.user,
        'nombre_usuario': request.user.first_name or request.user.username,
    })

#
#  Mesero  Vistas HTML protegidas MEJORADAS
#

#  Panel mesero MEJORADO con pestaas y auto-actualizacin
@ensure_csrf_cookie
def panel_mesero(request):
    """Panel mesero mejorado con pestaas de pedidos y reservas"""
    if not request.user.is_authenticated:
        messages.warning(request, 'Debes iniciar sesin para acceder al panel de mesero.')
        return redirect('/login/')

    context = {
        'user': request.user,
        'nombre_usuario': request.user.first_name or request.user.username,
        'title': 'Panel del Mesero',
        'user_role': 'mesero'
    }
    return render(request, 'mesero/panel_mesero.html', context)

#  NUEVO: Mapa de mesas para mesero
@login_required
def mapa_mesas_mesero(request):
    """Mapa visual de mesas para que el mesero seleccione y comande"""
    # Obtener todas las mesas con su informacin actualizada
    mesas = Mesa.objects.all().order_by('numero')

    # Serializar informacin de mesas
    mesas_data = []
    for mesa in mesas:
        from app.mesas.utils import obtener_info_mesa_completa
        info = obtener_info_mesa_completa(mesa)

        # Obtener pedido activo si existe
        pedido_activo = None
        if mesa.estado in ['ocupada', 'pagando']:
            pedido = Pedido.objects.filter(
                mesa=mesa,
                estado__in=['pendiente', 'en preparacion', 'listo']
            ).first()

            if pedido:
                pedido_activo = {
                    'id': pedido.id,
                    'personas': pedido.numero_personas,
                    'mesero': f"{pedido.mesero_comanda.first_name} {pedido.mesero_comanda.last_name}" if pedido.mesero_comanda else "N/A"
                }

        mesas_data.append({
            'numero': info['numero'],
            'estado': info['estado'],
            'capacidad': info['capacidad'],
            'disponible': info['disponible'],
            'es_combinada': info['es_combinada'],
            'display': info['display'],
            'pedido_activo': pedido_activo
        })

    context = {
        'user': request.user,
        'nombre_usuario': request.user.first_name or request.user.username,
        'title': 'Mapa de Mesas',
        'mesas': mesas_data
    }
    return render(request, 'mesero/mapa_mesas.html', context)

#  FUNCIN 1 CORREGIDA: api_pedidos_mesero
@login_required
def api_pedidos_mesero(request):
    """API para obtener pedidos del mesero (listos y entregados) - DJANGO AUTH"""
    try:
        logger.info(f" API Pedidos Mesero - Usuario: {request.user}")
        logger.info(f" Usuario autenticado: {request.user.is_authenticated}")
        
        fecha_hoy = date.today()
        
        #  SOLUCIONADO: Usar 'detalles' en lugar de 'detallepedido_set'
        pedidos_listos = Pedido.objects.filter(
            estado='listo',
            fecha__date=fecha_hoy
        ).select_related('mesa').prefetch_related('detalles__producto').order_by('-fecha')
        
        pedidos_entregados = Pedido.objects.filter(
            estado='entregado',
            fecha__date=fecha_hoy
        ).select_related('mesa').prefetch_related('detalles__producto').order_by('-fecha')
        
        logger.info(f" Pedidos listos encontrados: {pedidos_listos.count()}")
        logger.info(f" Pedidos entregados encontrados: {pedidos_entregados.count()}")
        
        # Serializar pedidos listos
        pedidos_listos_data = []
        for pedido in pedidos_listos:
            try:
                #  SOLUCIONADO: Usar 'detalles' en lugar de 'detallepedido_set'
                productos = [detalle.producto.nombre for detalle in pedido.detalles.all()]
            except:
                productos = [f'Pedido Mesa {pedido.mesa.numero if pedido.mesa else "N/A"}']
                
            pedidos_listos_data.append({
                'id': pedido.id,
                'mesa': pedido.mesa.numero if pedido.mesa else 'Sin mesa',
                'tiempo': pedido.fecha.strftime('%H:%M'),
                'productos': productos,
                'total': f'Bs/ {pedido.total:.2f}',
                'forma_pago': pedido.forma_pago,
                'observaciones': getattr(pedido, 'observaciones', '') or ''
            })
        
        # Serializar pedidos entregados
        pedidos_entregados_data = []
        for pedido in pedidos_entregados:
            try:
                #  SOLUCIONADO: Usar 'detalles' en lugar de 'detallepedido_set'
                productos = [detalle.producto.nombre for detalle in pedido.detalles.all()]
            except:
                productos = [f'Pedido Mesa {pedido.mesa.numero if pedido.mesa else "N/A"}']
                
            pedidos_entregados_data.append({
                'id': pedido.id,
                'mesa': pedido.mesa.numero if pedido.mesa else 'Sin mesa',
                'tiempo': pedido.fecha.strftime('%H:%M'),
                'productos': productos,
                'total': f'Bs/ {pedido.total:.2f}',
                'forma_pago': pedido.forma_pago
            })
        
        response_data = {
            'success': True,
            'pedidos_listos': pedidos_listos_data,
            'pedidos_entregados': pedidos_entregados_data,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f" Enviando {len(pedidos_listos_data)} pedidos listos y {len(pedidos_entregados_data)} entregados")
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.info(f" Error en api_pedidos_mesero: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

#  FUNCIN 2 CORREGIDA: api_reservas_mesero
@login_required
def api_reservas_mesero(request):
    """API para obtener reservas del da para el mesero - DJANGO AUTH"""
    try:
        logger.debug("="*50)
        logger.info(f" API RESERVAS MESERO - Usuario: {request.user}")
        logger.info(f" Usuario autenticado: {request.user.is_authenticated}")
        logger.debug("="*50)
        
        # Obtener fecha actual
        fecha_hoy = timezone.now().date()
        fecha_manana = fecha_hoy + timedelta(days=1)
        
        logger.info(f" Fecha hoy: {fecha_hoy}")
        logger.info(f" Fecha maana: {fecha_manana}")
        
        # Obtener TODAS las reservas para debug
        todas_reservas = Reserva.objects.all()
        logger.info(f" TOTAL reservas en BD: {todas_reservas.count()}")
        
        for reserva in todas_reservas:
            logger.info(f"   Reserva #{reserva.id}: {reserva.nombre_completo} | {reserva.fecha_reserva} | {reserva.estado}")
        
        # Obtener reservas de hoy
        reservas_hoy = Reserva.objects.filter(
            fecha_reserva=fecha_hoy
        ).order_by('hora_reserva')
        
        logger.info(f" Reservas encontradas para HOY ({fecha_hoy}): {reservas_hoy.count()}")
        
        # Debug detallado de reservas de hoy
        for reserva in reservas_hoy:
            logger.info(f"   Reserva HOY #{reserva.id}: {reserva.nombre_completo}, {reserva.hora_reserva}, Estado: {reserva.estado}")
        
        # Prximas reservas (maana en adelante)
        reservas_proximas = Reserva.objects.filter(
            fecha_reserva__gte=fecha_manana
        ).order_by('fecha_reserva', 'hora_reserva')[:10]
        
        logger.info(f" Prximas reservas encontradas: {reservas_proximas.count()}")
        
        # Debug prximas reservas
        for reserva in reservas_proximas:
            logger.info(f"   Reserva PRXIMA #{reserva.id}: {reserva.nombre_completo}, {reserva.fecha_reserva}, {reserva.hora_reserva}")
        
        # Serializar reservas de hoy
        reservas_hoy_data = []
        for reserva in reservas_hoy:
            estado_info = {
                'pendiente': {'texto': 'Pendiente', 'color': 'warning'},
                'confirmada': {'texto': 'Confirmada', 'color': 'success'}, 
                'en_uso': {'texto': 'En Uso', 'color': 'primary'},
                'completada': {'texto': 'Completada', 'color': 'secondary'},
                'cancelada': {'texto': 'Cancelada', 'color': 'danger'}
            }
            
            estado_actual = estado_info.get(reserva.estado, {'texto': reserva.estado, 'color': 'secondary'})
            
            reserva_data = {
                'id': reserva.id,
                'numero_carnet': reserva.numero_carnet,
                'nombre': reserva.nombre_completo,
                'hora': reserva.hora_reserva.strftime('%H:%M'),
                'personas': reserva.numero_personas,
                'mesa': reserva.mesa.numero if reserva.mesa else None,
                'telefono': reserva.telefono or 'No disponible',
                'email': reserva.email or 'No disponible',
                'estado': reserva.estado,
                'estado_texto': estado_actual['texto'],
                'estado_color': estado_actual['color'],
                'observaciones': reserva.observaciones or '',
                'fecha_creacion': reserva.fecha_creacion.strftime('%H:%M') if reserva.fecha_creacion else ''
            }
            
            reservas_hoy_data.append(reserva_data)
            logger.info(f"   Serializada reserva HOY: {reserva.nombre_completo} - {reserva.estado}")
        
        # Serializar prximas reservas
        reservas_proximas_data = []
        for reserva in reservas_proximas:
            reserva_data = {
                'id': reserva.id,
                'numero_carnet': reserva.numero_carnet,
                'nombre': reserva.nombre_completo,
                'fecha': reserva.fecha_reserva.strftime('%d/%m/%Y'),
                'hora': reserva.hora_reserva.strftime('%H:%M'),
                'personas': reserva.numero_personas,
                'estado': reserva.estado,
                'telefono': reserva.telefono or 'No disponible',
                'mesa': reserva.mesa.numero if reserva.mesa else None
            }
            reservas_proximas_data.append(reserva_data)
            logger.info(f"   Serializada reserva PRXIMA: {reserva.nombre_completo}")
        
        response_data = {
            'success': True,
            'reservas_hoy': reservas_hoy_data,
            'reservas_proximas': reservas_proximas_data,
            'timestamp': datetime.now().isoformat(),
            'total_hoy': len(reservas_hoy_data),
            'total_proximas': len(reservas_proximas_data),
            'debug_info': {
                'total_reservas_bd': todas_reservas.count(),
                'fecha_consultada': str(fecha_hoy),
                'usuario': str(request.user)
            }
        }
        
        logger.info(f" RESPUESTA FINAL:")
        logger.info(f"  - Reservas HOY: {len(reservas_hoy_data)}")
        logger.info(f"  - Reservas PRXIMAS: {len(reservas_proximas_data)}")
        logger.debug("="*50)
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.info(f" ERROR GRAVE en api_reservas_mesero: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'success': False,
            'error': str(e),
            'mensaje': 'Error al obtener las reservas'
        }, status=500)

#  FUNCIN 3 CORREGIDA: api_entregar_pedido
@login_required  
def api_entregar_pedido(request, pedido_id):
    """API para marcar un pedido como entregado - DJANGO AUTH"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Mtodo no permitido'}, status=405)
        
    try:
        pedido = Pedido.objects.get(id=pedido_id)
        
        if pedido.estado != 'listo':
            return JsonResponse({
                'success': False,
                'error': 'Solo se pueden entregar pedidos que estn listos'
            }, status=400)
        
        pedido.estado = 'entregado'
        pedido.save()
        
        logger.info(f" Pedido #{pedido_id} marcado como entregado por {request.user}")
        
        return JsonResponse({
            'success': True,
            'message': f'Pedido #{pedido_id} marcado como entregado',
            'pedido_id': pedido_id
        })
        
    except Pedido.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Pedido no encontrado'
        }, status=404)
    except Exception as e:
        logger.info(f" Error en api_entregar_pedido: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

#  FUNCIN 4 CORREGIDA: api_confirmar_reserva
@login_required
def api_confirmar_reserva(request, reserva_id):
    """API para confirmar una reserva - DJANGO AUTH"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Mtodo no permitido'}, status=405)
        
    try:
        reserva = Reserva.objects.get(id=reserva_id)
        
        if reserva.estado not in ['pendiente']:
            return JsonResponse({
                'success': False,
                'error': 'Solo se pueden confirmar reservas pendientes'
            }, status=400)
        
        reserva.estado = 'confirmada'
        reserva.save()
        
        logger.info(f" Reserva #{reserva_id} confirmada por {request.user}")
        
        return JsonResponse({
            'success': True,
            'message': f'Reserva #{reserva_id} confirmada',
            'reserva_id': reserva_id,
            'nuevo_estado': 'confirmada'
        })
        
    except Reserva.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Reserva no encontrada'
        }, status=404)
    except Exception as e:
        logger.info(f" Error en api_confirmar_reserva: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

#  FUNCIN 5 CORREGIDA: api_cambiar_estado_reserva
@login_required
def api_cambiar_estado_reserva(request, reserva_id):
    """API para cambiar el estado de una reserva - DJANGO AUTH"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Mtodo no permitido'}, status=405)
        
    try:
        import json
        data = json.loads(request.body) if request.body else {}
        nuevo_estado = data.get('estado')
        
        if not nuevo_estado:
            return JsonResponse({
                'success': False,
                'error': 'Estado requerido'
            }, status=400)
        
        estados_validos = ['pendiente', 'confirmada', 'en_uso', 'completada', 'cancelada']
        if nuevo_estado not in estados_validos:
            return JsonResponse({
                'success': False,
                'error': f'Estado invlido. Estados vlidos: {", ".join(estados_validos)}'
            }, status=400)
        
        reserva = Reserva.objects.get(id=reserva_id)
        estado_anterior = reserva.estado
        reserva.estado = nuevo_estado
        reserva.save()
        
        logger.info(f" Reserva #{reserva_id} cambiada de '{estado_anterior}' a '{nuevo_estado}' por {request.user}")
        
        return JsonResponse({
            'success': True,
            'message': f'Reserva #{reserva_id} actualizada a {nuevo_estado}',
            'reserva_id': reserva_id,
            'estado_anterior': estado_anterior,
            'nuevo_estado': nuevo_estado
        })
        
    except Reserva.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Reserva no encontrada'
        }, status=404)
    except Exception as e:
        logger.info(f" Error en api_cambiar_estado_reserva: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

#  FUNCIN 6 CORREGIDA: api_asignar_mesa_reserva
@login_required
def api_asignar_mesa_reserva(request, reserva_id):
    """API para asignar mesa a una reserva - DJANGO AUTH"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Mtodo no permitido'}, status=405)
        
    try:
        import json
        data = json.loads(request.body) if request.body else {}
        mesa_numero = data.get('mesa_numero')
        
        if not mesa_numero:
            return JsonResponse({
                'success': False,
                'error': 'Nmero de mesa requerido'
            }, status=400)
        
        reserva = Reserva.objects.get(id=reserva_id)
        
        try:
            mesa = Mesa.objects.get(numero=mesa_numero)
        except Mesa.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'Mesa {mesa_numero} no encontrada'
            }, status=404)
        
        mesa_anterior = reserva.mesa.numero if reserva.mesa else None
        reserva.mesa = mesa
        reserva.save()
        
        logger.info(f" Mesa {mesa_numero} asignada a reserva #{reserva_id} por {request.user}")
        
        return JsonResponse({
            'success': True,
            'message': f'Mesa {mesa_numero} asignada a la reserva',
            'reserva_id': reserva_id,
            'mesa_anterior': mesa_anterior,
            'mesa_nueva': mesa_numero
        })
        
    except Reserva.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Reserva no encontrada'
        }, status=404)
    except Exception as e:
        logger.info(f" Error en api_asignar_mesa_reserva: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# 
#  APIs COCINA CORREGIDAS - DJANGO AUTH
# 

#  NUEVA FUNCIN PARA REEMPLAZAR PedidosEnCocinaAPIView
@login_required
def pedidos_en_cocina_api(request):
    """API para obtener todos los pedidos para la cocina - DJANGO AUTH"""
    try:
        #  Debug: Verificar el usuario y rol
        logger.info(f" API Cocina - Usuario autenticado: {request.user}")
        logger.info(f" Username: {request.user.username}")
        
        #  CORREGIDO: Solo mostrar pedidos que el cocinero necesita trabajar
        # Excluir 'listo' y 'entregado' porque ya no son responsabilidad del cocinero
        pedidos = Pedido.objects.filter(
            estado__in=['pendiente', 'en preparacion']  #  SOLO ESTOS ESTADOS
        ).order_by('-fecha')
        
        logger.info(f" Pedidos encontrados para cocina: {pedidos.count()}")
        
        pedidos_data = []
        for pedido in pedidos:
            logger.info(f" Procesando pedido ID: {pedido.id}, Mesa: {pedido.mesa}, Estado: {pedido.estado}")
            
            #  SOLUCIONADO: Usar 'detalles' en lugar de 'detallepedido_set'
            try:
                detalles = pedido.detalles.all()  #  CORREGIDO
                if detalles.exists():
                    detalles_data = []
                    for detalle in detalles:
                        detalles_data.append({
                            'cantidad': detalle.cantidad,
                            'producto': detalle.producto.nombre if detalle.producto else 'Producto',
                            'subtotal': float(detalle.subtotal)
                        })
                    logger.info(f"   Detalles encontrados: {len(detalles_data)}")
                else:
                    # Si no hay detalles, crear uno genrico
                    detalles_data = [
                        {
                            'cantidad': 1,
                            'producto': f'Pedido para mesa {pedido.mesa.numero if pedido.mesa else "N/A"}',
                            'subtotal': float(pedido.total)
                        }
                    ]
                    logger.info(f"   No hay detalles, creando genrico")
            except Exception as e:
                logger.info(f"   Error obteniendo detalles: {str(e)}")
                # Fallback: usar datos bsicos
                detalles_data = [
                    {
                        'cantidad': 1,
                        'producto': f'Producto para mesa {pedido.mesa.numero if pedido.mesa else "N/A"}',
                        'subtotal': float(pedido.total)
                    }
                ]
            
            #  NUEVO: Informacin del mesero que comand
            mesero_nombre = "Cliente directo"
            if pedido.mesero_comanda:
                mesero_nombre = f"{pedido.mesero_comanda.first_name} {pedido.mesero_comanda.last_name}".strip() or pedido.mesero_comanda.username

            pedidos_data.append({
                'id': pedido.id,
                'mesa': pedido.mesa.numero if pedido.mesa else 'N/A',
                'estado': pedido.estado,
                'total': float(pedido.total),
                'fecha': pedido.fecha.isoformat(),
                'detalles': detalles_data,
                'numero_personas': pedido.numero_personas,
                'mesero': mesero_nombre
            })
        
        logger.info(f" Enviando {len(pedidos_data)} pedidos al frontend (solo pendientes y en preparacin)")
        return JsonResponse(pedidos_data, safe=False)
        
    except Exception as e:
        logger.info(f" ERROR GRAVE en pedidos_en_cocina_api: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'error': f'Error al obtener pedidos: {str(e)}',
            'mensaje_debug': 'Ver consola del servidor para detalles'
        }, status=500)

#  FUNCIN CORREGIDA: actualizar_estado_pedido
@login_required
def actualizar_estado_pedido(request, pedido_id):
    """Actualizar estado del pedido - DJANGO AUTH"""
    if request.method != 'PATCH':
        return JsonResponse({'error': 'Mtodo no permitido'}, status=405)
        
    try:
        import json
        data = json.loads(request.body) if request.body else {}
        
        logger.info(f" Actualizando pedido {pedido_id}, usuario: {request.user}")
        logger.info(f" Datos recibidos: {data}")
        
        # Buscar el pedido
        pedido = Pedido.objects.get(id=pedido_id)
        logger.info(f" Pedido encontrado: {pedido}")
        
        # Obtener el nuevo estado del request
        nuevo_estado = data.get('estado')
        logger.info(f" Nuevo estado solicitado: {nuevo_estado}")
        
        # Validar que se envi un estado
        if not nuevo_estado:
            return JsonResponse({
                'error': 'El campo "estado" es requerido'
            }, status=400)
        
        # Validar que el estado es vlido
        estados_validos = ['pendiente', 'en preparacion', 'listo', 'entregado']
        if nuevo_estado not in estados_validos:
            return JsonResponse({
                'error': f'Estado invlido. Estados vlidos: {", ".join(estados_validos)}'
            }, status=400)
        
        # Actualizar el estado
        estado_anterior = pedido.estado
        pedido.estado = nuevo_estado
        pedido.save()
        
        logger.info(f" Pedido {pedido_id} actualizado de '{estado_anterior}' a '{nuevo_estado}'")
        
        return JsonResponse({
            'mensaje': f'Pedido #{pedido_id} actualizado correctamente',
            'pedido_id': pedido.id,
            'estado_anterior': estado_anterior,
            'estado_nuevo': nuevo_estado
        })

    except Pedido.DoesNotExist:
        logger.info(f" Pedido {pedido_id} no encontrado")
        return JsonResponse({
            'error': f'Pedido con ID {pedido_id} no encontrado'
        }, status=404)
    
    except Exception as e:
        logger.info(f" Error al actualizar pedido {pedido_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'error': f'Error interno: {str(e)}'
        }, status=500)

# 
#  APIs RESTANTES (MANTENER ORIGINALES)
# 

# Funcin para obtener pedidos por mesa (para meseros)
@api_view(['GET'])
@permission_classes([IsAuthenticated])  #  Temporalmente sin EsMesero
def pedidos_por_mesa(request):
    """API para que el mesero vea pedidos por mesa"""
    try:
        logger.info(f" Mesero solicitando pedidos por mesa: {request.user}")
        
        # Obtener todas las mesas con pedidos activos
        pedidos = Pedido.objects.exclude(estado='entregado').select_related('mesa').order_by('-fecha')
        logger.info(f" Pedidos activos encontrados: {pedidos.count()}")
        
        # Agrupar por mesa
        mesas_data = {}
        for pedido in pedidos:
            mesa_numero = pedido.mesa.numero if pedido.mesa else 'Sin mesa'
            
            if mesa_numero not in mesas_data:
                mesas_data[mesa_numero] = {
                    'numero': mesa_numero,
                    'pedidos': []
                }
            
            mesas_data[mesa_numero]['pedidos'].append({
                'id': pedido.id,
                'estado': pedido.estado,
                'total': float(pedido.total),
                'fecha': pedido.fecha.isoformat()
            })
        
        logger.info(f" Enviando datos de {len(mesas_data)} mesas")
        return Response(list(mesas_data.values()), status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.info(f" Error en pedidos_por_mesa: {str(e)}")
        return Response({
            'error': f'Error al obtener pedidos por mesa: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Funcin para marcar pedido como entregado (para meseros) - FUNCIN ORIGINAL
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])  #  Temporalmente sin EsMesero
def marcar_entregado(request, pedido_id):
    """Marcar pedido como entregado"""
    try:
        logger.info(f" Marcando pedido {pedido_id} como entregado, usuario: {request.user}")
        
        pedido = Pedido.objects.get(id=pedido_id)
        pedido.estado = 'entregado'
        pedido.save()
        
        logger.info(f" Pedido {pedido_id} marcado como entregado")
        
        return Response({
            'mensaje': f'Pedido #{pedido_id} marcado como entregado'
        }, status=status.HTTP_200_OK)
        
    except Pedido.DoesNotExist:
        logger.info(f" Pedido {pedido_id} no encontrado para marcar como entregado")
        return Response({
            'error': f'Pedido con ID {pedido_id} no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.info(f" Error al marcar como entregado: {str(e)}")
        return Response({
            'error': f'Error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#  CRUD completo (opcional si usas routers)
class PedidoViewSet(viewsets.ModelViewSet):
    queryset = Pedido.objects.all().order_by('-fecha')
    serializer_class = PedidoSerializer
    permission_classes = [IsAuthenticated]

# 
#  MODIFICACIN DE PEDIDOS CON STOCK
# 

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def modificar_pedido_api(request, pedido_id):
    """
    API para modificar un pedido existente con control de stock.
    Permite agregar, eliminar o cambiar cantidades de productos.

    Body: {
        "productos": {
            "1": 3,  # producto_id: cantidad
            "2": 1,
            ...
        }
    }
    """
    try:
        from .utils import modificar_pedido_con_stock
        import json

        logger.info(f"Usuario {request.user} solicitando modificacin de pedido #{pedido_id}")

        # Obtener productos desde el request
        productos_nuevos = request.data.get('productos', {})

        if not productos_nuevos:
            return Response({
                'error': 'Debe proporcionar al menos un producto'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Convertir claves a int si vienen como strings
        productos_nuevos = {
            int(k): int(v) for k, v in productos_nuevos.items()
        }

        # Llamar a la funcin de modificacin con el usuario actual
        resultado = modificar_pedido_con_stock(pedido_id, productos_nuevos, usuario=request.user)

        return Response({
            'success': True,
            'mensaje': resultado['mensaje'],
            'pedido_id': pedido_id,
            'nuevo_total': resultado['nuevo_total']
        }, status=status.HTTP_200_OK)

    except ValueError as e:
        logger.warning(f"Error de validacin modificando pedido #{pedido_id}: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.exception(f"Error grave modificando pedido #{pedido_id}: {str(e)}")
        return Response({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def eliminar_producto_pedido_api(request, pedido_id, producto_id):
    """
    API para eliminar un producto especfico de un pedido.
    Solo elimina la cantidad NO pagada. Si todo est pagado, devuelve error.
    """
    try:
        from .utils import eliminar_producto_de_pedido

        logger.info(
            f"Usuario {request.user} eliminando producto {producto_id} "
            f"del pedido #{pedido_id}"
        )

        resultado = eliminar_producto_de_pedido(pedido_id, producto_id)

        return Response({
            'success': True,
            'mensaje': resultado['mensaje'],
            'nuevo_total': resultado['nuevo_total']
        }, status=status.HTTP_200_OK)

    except ValueError as e:
        logger.warning(f"Error eliminando producto: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.exception(f"Error grave eliminando producto de pedido: {str(e)}")
        return Response({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def resumen_modificacion_pedido_api(request, pedido_id):
    """
    API para obtener informacin detallada del pedido antes de modificarlo.
    Muestra qu productos pueden ser modificados y cules estn pagados.
    """
    try:
        from .utils import obtener_resumen_modificacion

        logger.info(f"Usuario {request.user} consultando resumen de pedido #{pedido_id}")

        resumen = obtener_resumen_modificacion(pedido_id)

        return Response(resumen, status=status.HTTP_200_OK)

    except ValueError as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.exception(f"Error obteniendo resumen de pedido: {str(e)}")
        return Response({
            'error': f'Error interno del servidor: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)