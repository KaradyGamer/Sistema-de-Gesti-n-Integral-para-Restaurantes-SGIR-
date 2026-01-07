from django.shortcuts import render, redirect
from django.contrib import messages
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
from app.reservas.models import Reserva

from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie

#  Configurar logger
logger = logging.getLogger('app.pedidos')

# ============================================
# ENDPOINT DESHABILITADO: Creación pública
# ============================================
@api_view(['POST', 'GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def crear_pedido_deshabilitado(request):
    """
    ❌ ENDPOINT DESHABILITADO

    El cliente QR ahora es SOLO LECTURA (menú digital).
    Los pedidos se crean ÚNICAMENTE por staff autenticado (meseros).

    Razón: Seguridad - Prevenir spam/DoS + Control total por staff
    Fecha: 2026-01-04
    """
    logger.warning(
        f"AUDIT_DENY endpoint=pedidos.cliente.crear "
        f"ip={request.META.get('REMOTE_ADDR', 'unknown')} "
        f"user_agent={request.META.get('HTTP_USER_AGENT', 'unknown')[:100]} "
        f"ts={timezone.now().isoformat()}"
    )

    return Response({
        'detail': 'Not found.'
    }, status=status.HTTP_404_NOT_FOUND)

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

# ============================================
# ❌ FUNCIÓN DESHABILITADA - NO USAR
# ============================================
# Esta función está DESHABILITADA desde 2026-01-04
# Razón: Cliente QR ahora es SOLO LECTURA
# Reemplazo: Pedidos se crean por staff autenticado (meseros)
# Preservada para referencia histórica
# ============================================

# FUNCIN CORREGIDA PARA CREAR PEDIDOS DEL CLIENTE (DESHABILITADA)
# @api_view(['POST'])
# @authentication_classes([])  # ❌ PELIGROSO: Sin autenticación
# @permission_classes([AllowAny])  # ❌ PELIGROSO: Acceso público
# @transaction.atomic
def crear_pedido_cliente_DESHABILITADO(request):
    """
    Crear pedido desde el cliente - VERSIN CORREGIDA PARA COMPATIBILIDAD
    """
    try:
        logger.info("Creando pedido del cliente")
        logger.debug(f"Datos recibidos: {request.data}")
        logger.debug(f"Mtodo: {request.method}, Content-Type: {request.content_type}")
        
        #  CORREGIDO: Obtener datos con mltiples nombres posibles
        mesa_id = (
            request.data.get('mesa_id') or 
            request.data.get('mesa') or 
            request.data.get('numero_mesa')
        )
        
        productos_data = (
            request.data.get('productos') or 
            request.data.get('detalles') or 
            []
        )
        
        forma_pago = request.data.get('forma_pago', 'efectivo')
        total_enviado = request.data.get('total', 0)

        #  NUEVO: Capturar mesero y nmero de personas
        mesero_id = request.data.get('mesero_id') or request.data.get('usuario_id')
        numero_personas = request.data.get('numero_personas')

        logger.debug(f"Mesa ID: {mesa_id}, Productos: {len(productos_data)}, Forma pago: {forma_pago}, Total: {total_enviado}, Mesero: {mesero_id}, Personas: {numero_personas}")

        #  Validaciones bsicas
        if not mesa_id:
            return Response({
                'error': 'El nmero de mesa es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not productos_data or len(productos_data) == 0:
            return Response({
                'error': 'Debe incluir al menos un producto en el pedido'
            }, status=status.HTTP_400_BAD_REQUEST)

        #  NUEVO: Validar nmero de personas (#6)
        if not numero_personas or int(numero_personas) < 1:
            return Response({
                'error': 'El nmero de personas debe ser al menos 1'
            }, status=status.HTTP_400_BAD_REQUEST)

        numero_personas = int(numero_personas)

        #  CORREGIDO: Buscar la mesa con select_for_update para evitar condiciones de carrera
        try:
            # Intentar primero por nmero (ms comn) con bloqueo de fila
            mesa = Mesa.objects.select_for_update().get(numero=mesa_id)
            logger.debug(f"Mesa encontrada por nmero (con bloqueo): {mesa}")
        except Mesa.DoesNotExist:
            try:
                # Fallback: intentar por ID con bloqueo de fila
                mesa = Mesa.objects.select_for_update().get(id=mesa_id)
                logger.debug(f"Mesa encontrada por ID (con bloqueo): {mesa}")
            except Mesa.DoesNotExist:
                logger.warning(f"Mesa {mesa_id} no encontrada")
                return Response({
                    'error': f'Mesa {mesa_id} no encontrada'
                }, status=status.HTTP_404_NOT_FOUND)

        #  NUEVO: Validar que la mesa est disponible (#3)
        if mesa.estado != 'disponible':
            return Response({
                'error': f'Mesa {mesa.numero} no est disponible (estado actual: {mesa.get_estado_display()})'
            }, status=status.HTTP_400_BAD_REQUEST)

        #  NUEVO: Verificar que no haya pedido activo en la mesa (#3)
        pedido_existente = Pedido.objects.filter(
            mesa=mesa,
            estado__in=[
                Pedido.ESTADO_CREADO,
                Pedido.ESTADO_CONFIRMADO,
                Pedido.ESTADO_EN_PREPARACION,
                Pedido.ESTADO_LISTO
            ]
        ).exists()

        if pedido_existente:
            return Response({
                'error': f'Mesa {mesa.numero} ya tiene un pedido activo'
            }, status=status.HTTP_409_CONFLICT)

        #  NUEVO: Validar capacidad de la mesa (#6)
        capacidad_real = mesa.capacidad_combinada if mesa.es_combinada else mesa.capacidad
        if numero_personas > capacidad_real:
            return Response({
                'error': f'Mesa {mesa.numero} solo tiene capacidad para {capacidad_real} personas. Solicitado: {numero_personas}'
            }, status=status.HTTP_400_BAD_REQUEST)

        #  Obtener mesero si se proporcion ID
        mesero = None
        if mesero_id:
            from app.usuarios.models import Usuario
            try:
                mesero = Usuario.objects.get(id=mesero_id)
            except Usuario.DoesNotExist:
                logger.warning(f"Mesero ID {mesero_id} no encontrado")

        #  Crear el pedido con mesero y nmero de personas (usando estado válido)
        pedido = Pedido.objects.create(
            mesa=mesa,
            fecha=timezone.now(),
            forma_pago=forma_pago,
            estado=Pedido.ESTADO_CREADO,  # FIX: 'pendiente' → ESTADO_CREADO
            mesero_comanda=mesero,
            numero_personas=numero_personas
        )

        #  NUEVO: Cambiar estado de la mesa a 'ocupada'
        mesa.estado = 'ocupada'
        mesa.save()

        mesero_nombre = f"{mesero.first_name} {mesero.last_name}" if mesero else "N/A"
        logger.info(f"Pedido #{pedido.id} creado - Mesa {mesa.numero} - {numero_personas} personas - Mesero: {mesero_nombre}")

        total_calculado = 0
        detalles_creados = []
        
        #  CORREGIDO: Procesar productos con mltiples formatos
        for item in productos_data:
            # Obtener ID del producto con mltiples nombres posibles
            producto_id = (
                item.get('producto_id') or
                item.get('producto') or
                item.get('id')
            )

            cantidad = int(item.get('cantidad', 1))

            if not producto_id:
                logger.warning(f"Item sin producto ID: {item}")
                continue

            try:
                producto = Producto.objects.get(id=producto_id)

                #  NUEVO: Descontar stock ANTES de crear el detalle (#2)
                stock_descontado = producto.descontar_stock(cantidad)

                if not stock_descontado:
                    # Stock insuficiente
                    logger.warning(f"Stock insuficiente de {producto.nombre}. Disponible: {producto.stock_actual}, Solicitado: {cantidad}")

                    # Si requiere inventario y no hay stock, fallar
                    if producto.requiere_inventario:
                        # Rollback: eliminar pedido creado
                        pedido.delete()
                        mesa.estado = 'disponible'  # Restaurar estado
                        mesa.save()

                        return Response({
                            'error': f'Stock insuficiente de {producto.nombre}. Disponible: {producto.stock_actual}, Solicitado: {cantidad}'
                        }, status=status.HTTP_400_BAD_REQUEST)

                subtotal = producto.precio * cantidad
                total_calculado += subtotal

                #  NUEVO: Crear detalle del pedido con precio_unitario explcito
                DetallePedido.objects.create(
                    pedido=pedido,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario=producto.precio,  #  Snapshot del precio actual
                    subtotal=subtotal
                )

                detalles_creados.append({
                    'producto': producto.nombre,
                    'cantidad': cantidad,
                    'precio_unitario': float(producto.precio),
                    'subtotal': float(subtotal),
                    'stock_restante': producto.stock_actual if producto.requiere_inventario else None
                })

                logger.debug(f"Detalle: {cantidad}x {producto.nombre} = Bs/ {subtotal} (Stock restante: {producto.stock_actual if producto.requiere_inventario else 'N/A'})")

            except Producto.DoesNotExist:
                logger.error(f"Producto ID {producto_id} no encontrado")
                # Continuar con los otros productos en lugar de fallar completamente
                continue

        #  Verificar que se crearon detalles
        if not detalles_creados:
            pedido.delete()  # Limpiar pedido sin detalles
            return Response({
                'error': 'No se pudieron procesar los productos del pedido'
            }, status=status.HTTP_400_BAD_REQUEST)

        #  Actualizar total del pedido
        pedido.total = total_calculado
        pedido.save()

        mesero_nombre_completo = f"{mesero.first_name} {mesero.last_name}" if mesero else "Cliente directo"
        logger.info(f"Pedido #{pedido.id} completado - Mesa {mesa.numero} - Total: Bs/ {total_calculado}")

        return Response({
            'success': True,
            'mensaje': 'Pedido creado exitosamente',
            'pedido_id': pedido.id,
            'mesa': mesa.numero,
            'numero_personas': numero_personas,
            'mesero': mesero_nombre_completo,
            'total': float(total_calculado),
            'detalles': detalles_creados,
            'estado': pedido.estado
        }, status=status.HTTP_201_CREATED)

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
                estado__in=[
                    Pedido.ESTADO_CREADO,
                    Pedido.ESTADO_CONFIRMADO,
                    Pedido.ESTADO_EN_PREPARACION,
                    Pedido.ESTADO_LISTO
                ]
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
            except Exception as e:
                logger.warning(f"Error al obtener productos del pedido {pedido.id}: {e}")
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
            except Exception as e:
                logger.warning(f"Error al obtener productos del pedido {pedido.id}: {e}")
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
        
        logger.info(" RESPUESTA FINAL:")
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
        from app.pedidos.utils import validar_transicion_estado

        pedido = Pedido.objects.get(id=pedido_id)

        # ✅ PATCH-002: Validar transición ANTES de asignar, usar constante
        try:
            validar_transicion_estado(pedido.estado, Pedido.ESTADO_ENTREGADO)
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

        pedido.estado = Pedido.ESTADO_ENTREGADO
        pedido.save()

        logger.info(f" Pedido #{pedido_id} marcado como entregado por {request.user}")

        # ✅ LOGGING DE AUDITORÍA
        logger.info(
            f"AUDIT pedido_entregado "
            f"pedido_id={pedido.id} "
            f"user={getattr(request.user, 'username', 'anon')} "
            f"user_id={getattr(request.user, 'id', None)} "
            f"mesa={pedido.mesa.numero if pedido.mesa else 'N/A'} "
            f"ts={timezone.now().isoformat()}"
        )

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
            estado__in=[
                Pedido.ESTADO_CREADO,
                Pedido.ESTADO_CONFIRMADO,
                Pedido.ESTADO_EN_PREPARACION
            ]  #  SOLO ESTOS ESTADOS
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
                    logger.info("   No hay detalles, creando genrico")
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
        
        from app.pedidos.utils import validar_transicion_estado

        # Obtener el nuevo estado del request
        nuevo_estado = data.get('estado')
        logger.info(f" Nuevo estado solicitado: {nuevo_estado}")

        # Validar que se envi un estado
        if not nuevo_estado:
            return JsonResponse({
                'error': 'El campo "estado" es requerido'
            }, status=400)

        # ✅ RONDA 2 + 3B: Bloquear cierre manual (solo desde caja)
        if nuevo_estado == 'cerrado':
            return JsonResponse({
                'error': 'El cierre de pedidos solo se realiza desde el módulo de Caja'
            }, status=403)

        # ✅ RONDA 2: Validar transición de estado
        estado_anterior = pedido.estado
        try:
            validar_transicion_estado(estado_anterior, nuevo_estado)
        except ValueError as e:
            return JsonResponse({
                'error': str(e)
            }, status=400)

        # Actualizar el estado
        pedido.estado = nuevo_estado
        pedido.save()

        logger.info(f" Pedido {pedido_id} actualizado de '{estado_anterior}' a '{nuevo_estado}'")

        # ✅ LOGGING DE AUDITORÍA
        logger.info(
            f"AUDIT pedido_estado "
            f"pedido_id={pedido.id} "
            f"user={getattr(request.user, 'username', 'anon')} "
            f"user_id={getattr(request.user, 'id', None)} "
            f"estado_anterior={estado_anterior} "
            f"estado_nuevo={nuevo_estado} "
            f"mesa={pedido.mesa.numero if pedido.mesa else 'N/A'} "
            f"ts={timezone.now().isoformat()}"
        )

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
    """Marcar pedido como entregado - LEGACY: usar api_entregar_pedido (L613) en su lugar"""
    try:
        logger.info(f" Marcando pedido {pedido_id} como entregado, usuario: {request.user}")

        pedido = Pedido.objects.get(id=pedido_id)

        # ✅ RONDA 2 HARDENING: Validar transición de estado
        from app.pedidos.utils import validar_transicion_estado
        try:
            validar_transicion_estado(pedido.estado, Pedido.ESTADO_ENTREGADO)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        pedido.estado = Pedido.ESTADO_ENTREGADO
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

# ============================================
# RONDA 3A: CANCELACIÓN DE PEDIDO
# ============================================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancelar_pedido(request, pedido_id):
    """
    Cancela un pedido y devuelve el stock si ya fue descontado.

    Reglas:
    - Solo pedidos en estado: creado, confirmado, en_preparacion, listo
    - NO se pueden cancelar pedidos: entregado, cerrado
    - Si el pedido está en preparación/listo, requiere autorización superior
    - Motivo de cancelación obligatorio
    """
    from app.pedidos.utils import devolver_stock_pedido, validar_transicion_estado
    from django.utils import timezone

    try:
        motivo = request.data.get('motivo')

        if not motivo:
            return Response(
                {'error': 'Motivo de cancelación obligatorio'},
                status=status.HTTP_400_BAD_REQUEST
            )

        pedido = Pedido.objects.get(id=pedido_id)

        # ✅ RONDA 2: Validar transición de estado
        try:
            validar_transicion_estado(pedido.estado, 'cancelado')
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 🔐 Si ya pasó por cocina, requiere autorización superior
        if pedido.estado in ['en_preparacion', 'listo']:
            if not request.user.is_superuser:
                return Response(
                    {'error': 'Se requiere autorización de administrador para cancelar pedidos en preparación o listos'},
                    status=status.HTTP_403_FORBIDDEN
                )

        estado_anterior = pedido.estado

        # ✅ PATCH-002: Validar transición ANTES de cambiar estado
        from app.pedidos.utils import validar_transicion_estado
        try:
            validar_transicion_estado(pedido.estado, Pedido.ESTADO_CANCELADO)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ DEVOLVER STOCK
        productos_restaurados = devolver_stock_pedido(pedido)

        # Cambiar estado
        pedido.estado = Pedido.ESTADO_CANCELADO
        pedido.motivo_cancelacion = motivo
        pedido.save()

        logger.info(
            f"AUDIT pedido_cancelado pedido_id={pedido.id} "
            f"user={request.user.username} "
            f"user_id={request.user.id} "
            f"estado_anterior={estado_anterior} "
            f"productos_restaurados={productos_restaurados} "
            f"motivo='{motivo}' "
            f"ts={timezone.now().isoformat()}"
        )

        return Response({
            'success': True,
            'mensaje': f'Pedido #{pedido_id} cancelado exitosamente',
            'productos_restaurados': productos_restaurados
        })

    except Pedido.DoesNotExist:
        return Response(
            {'error': f'Pedido #{pedido_id} no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    except Exception as e:
        logger.exception(f"Error cancelando pedido #{pedido_id}: {str(e)}")
        return Response(
            {'error': f'Error interno del servidor: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
